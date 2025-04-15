from flask import Blueprint, jsonify, request, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import csv
import json
import os
import time
import uuid
from datetime import datetime
from functools import wraps
from typing import Dict, List, Optional

# Create Blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Initialize rate limiter with memory storage
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    storage_options={},
    default_limits=["200 per day", "50 per hour"]
)

# API key storage
API_KEYS_FILE = 'api_keys.json'

# Load API keys from file
def load_api_keys():
    if os.path.exists(API_KEYS_FILE):
        try:
            with open(API_KEYS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading API keys: {str(e)}")
    return {"keys": {}}

# Save API keys to file
def save_api_keys(api_keys):
    try:
        with open(API_KEYS_FILE, 'w') as f:
            json.dump(api_keys, f, indent=2)
    except Exception as e:
        print(f"Error saving API keys: {str(e)}")

# Generate a new API key
def generate_api_key(name, email, tier="basic"):
    api_keys = load_api_keys()
    api_key = str(uuid.uuid4())
    
    api_keys["keys"][api_key] = {
        "name": name,
        "email": email,
        "tier": tier,
        "created_at": datetime.now().isoformat(),
        "last_used": None,
        "usage_count": 0
    }
    
    save_api_keys(api_keys)
    return api_key

# API key authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({"error": "API key is required"}), 401
        
        api_keys = load_api_keys()
        
        if api_key not in api_keys["keys"]:
            return jsonify({"error": "Invalid API key"}), 401
        
        # Update usage statistics
        api_keys["keys"][api_key]["last_used"] = datetime.now().isoformat()
        api_keys["keys"][api_key]["usage_count"] += 1
        save_api_keys(api_keys)
        
        return f(*args, **kwargs)
    return decorated_function

# Helper function to get rate limit based on tier
def get_rate_limit(api_key):
    api_keys = load_api_keys()
    
    if api_key in api_keys["keys"]:
        tier = api_keys["keys"][api_key]["tier"]
        if tier == "premium":
            return "300/minute"
        
    return "60/minute"  # Default basic tier

# Helper function to get all brands from CSV
def get_brands_from_csv():
    brands = {}
    brands_file = 'brands_devices.csv'
    
    if os.path.exists(brands_file):
        try:
            with open(brands_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 3:  # brand_name, device_name, device_url, device_image
                        brand_name = row[0]
                        if brand_name not in brands:
                            brands[brand_name] = {
                                "name": brand_name,
                                "devices": []
                            }
                        
                        device = {
                            "name": row[1],
                            "url": row[2],
                            "image": row[3] if len(row) > 3 else ""
                        }
                        
                        brands[brand_name]["devices"].append(device)
        except Exception as e:
            print(f"Error reading brands file: {str(e)}")
    
    return list(brands.values())

# Helper function to get devices from CSV
def get_devices_from_csv(brand_name=None, limit=100, offset=0):
    devices = []
    brands_file = 'brands_devices.csv'
    
    if os.path.exists(brands_file):
        try:
            with open(brands_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                
                for row in reader:
                    if len(row) >= 3:  # brand_name, device_name, device_url, device_image
                        if brand_name is None or row[0].lower() == brand_name.lower():
                            device = {
                                "brand": row[0],
                                "name": row[1],
                                "url": row[2],
                                "image": row[3] if len(row) > 3 else ""
                            }
                            devices.append(device)
        except Exception as e:
            print(f"Error reading brands file: {str(e)}")
    
    # Apply pagination
    total = len(devices)
    devices = devices[offset:offset+limit]
    
    return {
        "devices": devices,
        "total": total,
        "limit": limit,
        "offset": offset
    }

# Helper function to get device specifications
def get_device_specs(device_url):
    specs_file = 'device_specifications.csv'
    
    if os.path.exists(specs_file):
        try:
            with open(specs_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                
                for row in reader:
                    if len(row) >= 4 and row[0] == device_url:  # device_url, name, pictures, specifications
                        try:
                            specs = json.loads(row[3])
                            return specs
                        except:
                            return None
        except Exception as e:
            print(f"Error reading specs file: {str(e)}")
    
    return None

# Helper function to search devices
def search_devices(query, limit=100, offset=0):
    devices = []
    brands_file = 'brands_devices.csv'
    
    if os.path.exists(brands_file):
        try:
            with open(brands_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                
                for row in reader:
                    if len(row) >= 3:  # brand_name, device_name, device_url, device_image
                        if (query.lower() in row[0].lower() or  # Brand name
                            query.lower() in row[1].lower()):   # Device name
                            device = {
                                "brand": row[0],
                                "name": row[1],
                                "url": row[2],
                                "image": row[3] if len(row) > 3 else ""
                            }
                            devices.append(device)
        except Exception as e:
            print(f"Error reading brands file: {str(e)}")
    
    # Apply pagination
    total = len(devices)
    devices = devices[offset:offset+limit]
    
    return {
        "devices": devices,
        "total": total,
        "limit": limit,
        "offset": offset
    }

# API Routes

# Get all brands
@api_bp.route('/brands', methods=['GET'])
@require_api_key
@limiter.limit(lambda: get_rate_limit(request.headers.get('X-API-Key')))
def get_brands():
    try:
        brands = get_brands_from_csv()
        return jsonify({
            "status": "success",
            "brands": brands
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Get brand details
@api_bp.route('/brands/<brand_name>', methods=['GET'])
@require_api_key
@limiter.limit(lambda: get_rate_limit(request.headers.get('X-API-Key')))
def get_brand(brand_name):
    try:
        brands = get_brands_from_csv()
        
        for brand in brands:
            if brand["name"].lower() == brand_name.lower():
                return jsonify({
                    "status": "success",
                    "brand": brand
                })
        
        return jsonify({
            "status": "error",
            "message": f"Brand '{brand_name}' not found"
        }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Get all devices with pagination
@api_bp.route('/devices', methods=['GET'])
@require_api_key
@limiter.limit(lambda: get_rate_limit(request.headers.get('X-API-Key')))
def get_devices():
    try:
        brand = request.args.get('brand')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        result = get_devices_from_csv(brand, limit, offset)
        
        return jsonify({
            "status": "success",
            **result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Get device details
@api_bp.route('/devices/<path:device_url>', methods=['GET'])
@require_api_key
@limiter.limit(lambda: get_rate_limit(request.headers.get('X-API-Key')))
def get_device(device_url):
    try:
        # Ensure URL is properly formatted
        if not device_url.startswith('http'):
            device_url = f"https://www.gsmarena.com/{device_url}"
        
        specs = get_device_specs(device_url)
        
        if specs:
            return jsonify({
                "status": "success",
                "device": specs
            })
        
        return jsonify({
            "status": "error",
            "message": "Device not found"
        }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Search devices
@api_bp.route('/search', methods=['GET'])
@require_api_key
@limiter.limit(lambda: get_rate_limit(request.headers.get('X-API-Key')))
def search():
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        if not query:
            return jsonify({
                "status": "error",
                "message": "Search query is required"
            }), 400
        
        result = search_devices(query, limit, offset)
        
        return jsonify({
            "status": "success",
            **result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Admin routes for API key management
@api_bp.route('/admin/keys', methods=['POST'])
def create_api_key():
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'email' not in data:
            return jsonify({
                "status": "error",
                "message": "Name and email are required"
            }), 400
        
        tier = data.get('tier', 'basic')
        if tier not in ['basic', 'premium']:
            tier = 'basic'
        
        api_key = generate_api_key(data['name'], data['email'], tier)
        
        return jsonify({
            "status": "success",
            "api_key": api_key
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Get API usage statistics
@api_bp.route('/admin/stats', methods=['GET'])
def get_stats():
    try:
        api_keys = load_api_keys()
        
        stats = {
            "total_keys": len(api_keys["keys"]),
            "keys_by_tier": {
                "basic": 0,
                "premium": 0
            },
            "total_requests": 0,
            "keys": []
        }
        
        for key, data in api_keys["keys"].items():
            stats["keys_by_tier"][data["tier"]] += 1
            stats["total_requests"] += data["usage_count"]
            
            # Add key info (masked)
            masked_key = f"{key[:8]}...{key[-4:]}"
            stats["keys"].append({
                "key": masked_key,
                "name": data["name"],
                "email": data["email"],
                "tier": data["tier"],
                "created_at": data["created_at"],
                "last_used": data["last_used"],
                "usage_count": data["usage_count"]
            })
        
        return jsonify({
            "status": "success",
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
