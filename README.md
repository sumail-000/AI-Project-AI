# AI-Powered Mobile Device Information System

A comprehensive system for managing, analyzing, and providing intelligent access to mobile device information through a web interface and API.

## Core Features

### 1. Device Data Management
- **Automated Data Collection**: Scraping and updating device information from GSMArena
- **Brand Management**: Comprehensive brand scanning and device cataloging
- **Incremental Updates**: Smart system for keeping device data current
- **Data Caching**: Efficient caching mechanism for improved performance

### 2. AI-Powered Device Assistant
- **Natural Language Processing**: Advanced understanding of device-related queries
- **Smart Search**: Context-aware device search and comparison
- **Specification Analysis**: Detailed analysis of device specifications
- **Recommendation Engine**: Intelligent device recommendations based on user preferences
- **Query Understanding**: Advanced intent recognition and entity extraction

### 3. Web Interface
- **Interactive Dashboard**: User-friendly interface for device queries
- **Real-time Search**: Instant device search and comparison
- **Progress Tracking**: Real-time monitoring of data updates
- **Data Preview**: Preview and manage device information
- **API Management**: Monitor and manage API usage

### 4. RESTful API
- **Device Search**: Search for devices with various parameters
- **Device Comparison**: Compare multiple devices side-by-side
- **Specification Lookup**: Get detailed device specifications
- **Recommendations**: Get personalized device recommendations
- **Rate Limiting**: Controlled API access with rate limiting

## Technical Architecture

### Core Components
- **Web Application** (`app.py`): Flask-based web interface and API endpoints
- **AI Assistant** (`ai_assistant.py`): Intelligent device query processing
- **Data Scraping** (`scraper.py`): Device data collection from GSMArena
- **Brand Management** (`brand_scanner.py`): Brand and device cataloging
- **Incremental Updates** (`incremental_scraper.py`): Smart data updates
- **API Layer** (`api.py`): RESTful API implementation
- **Response Templates** (`responses.py`): AI assistant response patterns

### Data Storage
- **Device Database**: CSV-based storage of device information
- **Brand Cache**: JSON-based caching of brand data
- **Update Tracking**: JSON-based tracking of device updates
- **API Keys**: Secure storage of API credentials

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd AI-Project-AI
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the system:
- Create a `.env` file with necessary configurations
- Update `api_keys.json` with required API credentials
- Ensure data files (`brands_devices.csv`, `device_specifications.csv`) are in place

## Usage

### Starting the System
```bash
python app.py
```
Access the web interface at `http://localhost:5000`

### Web Interface Features
- **Home Page**: Main dashboard with search and quick access
- **Device Search**: Search for devices by name, brand, or specifications
- **Device Comparison**: Compare multiple devices side-by-side
- **API Management**: Monitor and manage API usage
- **Data Management**: Preview and manage device data

### API Endpoints
- `POST /api/device-search`: Search for devices
- `POST /api/device-comparison`: Compare multiple devices
- `POST /api/device-recommendations`: Get device recommendations
- `POST /api/device-specifications`: Get detailed device specifications

## Project Structure

```
AI-Project-AI/
├── app.py                 # Main web application
├── ai_assistant.py        # AI assistant implementation
├── responses.py           # Response templates
├── scraper.py            # Device data scraping
├── brand_scanner.py      # Brand management
├── incremental_scraper.py # Incremental updates
├── api.py                # API implementation
├── conversation_model.py  # Conversation handling
├── requirements.txt      # Project dependencies
├── templates/            # Web interface templates
├── static/              # Static assets
├── conversation_data/   # Training data
├── brands_devices.csv   # Device database
├── device_specifications.csv # Device specifications
├── brands_cache.json    # Brand cache
└── device_updates.json  # Update tracking
```

## Dependencies

- Flask: Web framework
- Pandas: Data manipulation
- Numpy: Numerical computing
- Loguru: Advanced logging
- Transformers: NLP models
- Scikit-learn: Machine learning
- NLTK: Natural language processing
- Aiohttp: Async HTTP client
- And more (see requirements.txt)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License

```
MIT License

Copyright (c) 2024 AI-Project-AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Important Notes

1. **Data Usage**: The license covers the software code but does not grant rights to the device data collected through the scraper. Users must comply with GSMArena's terms of service when using the scraping functionality.

2. **API Keys**: Users are responsible for obtaining and managing their own API keys for any external services used by the system.

3. **Attribution**: When using this software, please provide appropriate attribution to the original authors.

4. **No Warranty**: The software is provided "as is" without any warranty of any kind.

## Support

For support, please [provide contact information or issue reporting guidelines]
