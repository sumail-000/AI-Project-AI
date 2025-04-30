"""
Response templates for the AI assistant.
This module contains all the hardcoded responses used by the AI assistant,
separated from core logic for better maintainability.
"""

# Category-based response templates
CATEGORY_RESPONSES = {
    'greeting': [
        "Hello! I'm your mobile device assistant. How can I help you today?",
        "Hi there! Looking for information about mobile devices?",
        "Greetings! I'm here to help with all your mobile device questions.",
        "Welcome! I can help you find the perfect mobile device or answer questions about phones and tablets.",
        "Hello! Need help finding a new phone or information about a specific device?",
        "Hi! I'm your mobile tech expert. How can I assist you today?"
    ],
    'farewell': [
        "Goodbye! Feel free to return if you have more questions about mobile devices.",
        "See you later! I'm here whenever you need mobile device information.",
        "Until next time! Let me know if you need help with devices in the future.",
        "Take care! Come back anytime you need mobile device assistance.",
        "Goodbye! Happy to help with any future mobile device questions.",
        "Farewell! I'm always here to help with your smartphone and tablet questions."
    ],
    'thanks': [
        "You're welcome! Is there anything else you'd like to know about mobile devices?",
        "Happy to help! Let me know if you need more information.",
        "My pleasure! I'm here for all your mobile device questions.",
        "Glad I could assist! Any other mobile device questions I can answer?",
        "No problem at all! Feel free to ask if you need more details.",
        "You're welcome! I'm always happy to help with mobile device information."
    ],
    'device_search': [
        "I can help you find devices. What type of device are you looking for?",
        "Sure, I can search for devices. Any specific brand or features you're interested in?",
        "I'll help you find the perfect device. Could you give me more details about what you're looking for?",
        "Let's find the right device for you. Are you looking for something with a great camera, battery life, or performance?",
        "I can search our database for the perfect device. Do you have a preferred brand or price range?",
        "What features matter most to you in a mobile device? I can help find one that matches your needs."
    ],
    'comparison': [
        "I can compare devices for you. Which devices would you like to compare?",
        "Device comparison is my specialty. What models would you like to compare?",
        "Let's compare some devices. Which ones are you interested in?",
        "I'd be happy to compare different devices. Could you mention the specific models?",
        "Comparing devices can help you make the right choice. Which ones are you considering?",
        "I can show you a side-by-side comparison. Which devices would you like to see?"
    ],
    'specification': [
        "I can provide detailed specifications. Which device are you interested in?",
        "Specifications are important! Which device would you like to know more about?",
        "I have detailed specs on many devices. Which one are you looking at?",
        "I can tell you all about a device's specifications. Which one are you curious about?",
        "Looking for specific technical details? Which device do you want to know about?",
        "I have comprehensive specification data. Which device would you like me to detail?"
    ],
    'price': [
        "I can help with price information. Which device are you interested in?",
        "Price ranges vary by device and region. Which model are you asking about?",
        "Let me help you find price information. Which device are you looking at?",
        "I can provide pricing details. Which specific device are you considering?",
        "Interested in the cost of a device? Which one would you like to know about?",
        "I can help you understand the value proposition. Which device's price are you curious about?"
    ],
    'camera': [
        "Camera quality is important for many users. Which device's camera would you like to know about?",
        "I can tell you about camera specifications. Which device are you interested in?",
        "Looking for a great camera phone? I can help you find the best options.",
        "Do you need a phone with excellent photo capabilities? I can suggest some great choices."
    ],
    'battery': [
        "Battery life is crucial for mobile devices. Which one would you like to know about?",
        "I can tell you about battery specifications. Which device are you interested in?",
        "Looking for a phone with long battery life? I can suggest some options.",
        "Do you need a device that lasts all day? I can help you find one with great battery performance."
    ],
    'performance': [
        "Performance specs are important for power users. Which device are you curious about?",
        "I can tell you about processing power and speed. Which device interests you?",
        "Looking for a high-performance device? I can suggest some powerful options.",
        "Do you need a phone that can handle demanding apps and games? I can help you find one."
    ],
    'display': [
        "Screen quality makes a big difference in user experience. Which device's display would you like to know about?",
        "I can tell you about display specifications. Which device are you interested in?",
        "Looking for a phone with a great screen? I can suggest some excellent options.",
        "Do you need a device with vibrant colors or high refresh rate? I can help you find one."
    ],
    'identity': [
        "I'm your mobile device assistant, designed to help with device information, comparisons, and recommendations.",
        "I'm a specialized assistant for mobile devices. I can help you find information, compare models, and make recommendations.",
        "I'm an AI assistant focused on mobile devices. I have information on thousands of smartphones and tablets.",
        "I'm a mobile technology expert designed to help you find the perfect device and answer your questions.",
        "I'm your personal guide to the world of mobile devices, with detailed knowledge of specifications and features.",
        "Think of me as your mobile device encyclopedia and recommendation engine all in one."
    ],
    'general': [
        "I specialize in mobile device information. How can I assist you today?",
        "I can help with device specifications, comparisons, and recommendations. What are you looking for?",
        "As your mobile device assistant, I'm here to answer your questions. What would you like to know?",
        "I'm here to help with all your mobile device needs. What information are you looking for?",
        "I can provide details on smartphones, tablets, and their features. What can I help you with?",
        "Whether you need device information or buying advice, I'm here to assist. What's on your mind?"
    ],
    'help': [
        "I can help you with device information, specifications, comparisons, and recommendations. What would you like to know?",
        "You can ask me about specific phones, compare different models, or get recommendations based on your needs.",
        "Try asking about a phone's camera, battery life, or performance. Or ask me to recommend the best phones for your needs.",
        "Need assistance? You can ask questions like 'Tell me about the iPhone 14' or 'What are the best phones for photography?'"
    ]
}

# Fallback responses for different scenarios
FALLBACK_RESPONSES = {
    'no_recommendations': "Based on our database, I can recommend devices from popular brands like Samsung, Apple, Google, and more. Would you like to know about specific features like camera quality, battery life, or performance?",
    'no_device_found': "I couldn't find that specific device in our database. Could you check the spelling or try a different device?",
    'no_specs_found': "I couldn't find those specific specifications for this device. Would you like to know about other aspects of the device instead?",
    'general_error': "I'm sorry, I couldn't process that request. Could you please try again or ask in a different way?",
    'unclear_request': "I'm not sure I understood what you're looking for. Could you please provide more details or rephrase your question?",
    'too_general': "That's a bit broad. Could you be more specific about which device or feature you're interested in?",
    'no_comparison_devices': "I need to know which specific devices you'd like to compare. Could you mention at least two device models?",
    'limited_data': "I have limited information about this device. Would you like to know what data I do have available?",
    'outdated_info': "My information about this device might be outdated. Would you like me to share what I know with that caveat?",
    'multiple_devices_found': "I found multiple devices matching that description. Could you be more specific about which one you're interested in?",
    'no_price_info': "I don't have specific pricing information for this device, as prices vary by region and retailer. Would you like to know about its specifications instead?"
}

# Response templates for device information
DEVICE_TEMPLATES = {
    'found_device': "I found information about {brand_name} {device_name}. Would you like to know about its specifications, price, or something else?",
    'multiple_devices': "I found {count} devices matching '{search_term}'. Could you be more specific about which one you're interested in?",
    'recommendation_intro': "Here are some top phone recommendations based on the latest data:",
    'recommendation_specific': "Based on your interest in {feature}, here are some recommended devices:",
    'recommendation_price': "Here are some recommended {price_category} phones that offer great value:",
    'recommendation_brand': "Here are some of the best {brand} devices currently available:",
    'spec_intro': "Here are the {specs} specifications for the {device_name}:",
    'spec_highlight': "The {device_name} is especially notable for its {highlight_feature}.",
    'camera_highlight': "The {device_name} features {camera_specs}, making it excellent for photography.",
    'performance_highlight': "With {processor} and {ram} of RAM, the {device_name} delivers impressive performance.",
    'battery_highlight': "The {device_name} comes with a {battery_size} battery, offering {battery_life} of typical usage.",
    'display_highlight': "The {device_name} sports a {display_size} {display_type} display with {resolution} resolution.",
    'compare_intro': "Here's a comparison of {devices}:",
    'compare_winner': "Based on {criteria}, the {device_name} has an edge.",
    'popular_device': "The {device_name} is quite popular for its {popular_feature}.",
    'newest_device': "The {device_name} is one of the newer releases from {brand_name}, featuring {new_feature}.",
    'value_proposition': "If you're looking for {feature}, the {device_name} offers excellent value."
}

# Keywords for feature detection
FEATURE_KEYWORDS = {
    'high_end': ['best', 'top', 'premium', 'flagship', 'high-end', 'expensive', 'pro', 'ultimate', 'elite', 'luxury', 'high quality', 'professional'],
    'mid_range': ['mid-range', 'mid range', 'medium', 'balanced', 'good value', 'reasonably priced', 'middle tier', 'intermediate', 'mainstream', 'moderate', 'average price'],
    'budget': ['budget', 'cheap', 'affordable', 'inexpensive', 'low cost', 'entry level', 'basic', 'economical', 'value', 'bargain', 'low price', 'low-end'],
    'camera': ['camera', 'photography', 'pictures', 'photos', 'selfie', 'video', 'zoom', 'lens', 'megapixel', 'portrait', 'night mode', 'ultra-wide', 'telephoto', 'image quality', 'photographic', 'recording'],
    'battery': ['battery', 'long lasting', 'battery life', 'endurance', 'all day', 'charging', 'fast charge', 'power', 'stamina', 'capacity', 'mAh', 'wireless charging', 'battery drain', 'battery health'],
    'performance': ['fast', 'performance', 'speed', 'gaming', 'powerful', 'processor', 'cpu', 'gpu', 'chip', 'snapdragon', 'exynos', 'a15', 'bionic', 'benchmark', 'responsive', 'smooth', 'multitasking', 'lag free'],
    'display': ['screen', 'display', 'amoled', 'oled', 'lcd', 'big screen', 'resolution', 'refresh rate', 'hdr', 'bright', 'color', 'panel', 'viewing', 'retina', 'super amoled', 'dynamic amoled', 'fluid', '120hz', '90hz'],
    'storage': ['storage', 'space', 'capacity', 'gb', 'tb', 'memory', 'expandable', 'microsd', 'cloud storage', 'internal storage', 'data', 'fill up', 'store'],
    'design': ['design', 'build quality', 'premium feel', 'materials', 'glass', 'metal', 'plastic', 'weight', 'lightweight', 'compact', 'slim', 'thin', 'ergonomic', 'comfortable', 'look', 'aesthetic'],
    'software': ['software', 'android', 'ios', 'oneui', 'miui', 'os', 'operating system', 'interface', 'ui', 'updates', 'features', 'clean', 'stock', 'customization', 'theme'],
    'durability': ['durability', 'rugged', 'tough', 'waterproof', 'water resistant', 'ip68', 'ip67', 'drop', 'scratch resistant', 'gorilla glass', 'ceramic shield', 'robust', 'solid'],
    'connectivity': ['5g', 'wifi', 'bluetooth', 'nfc', 'usb', 'type-c', 'port', 'headphone jack', 'connection', 'cellular', 'network', 'wireless', 'hotspot'],
    'audio': ['sound', 'audio', 'speaker', 'stereo', 'dolby', 'headphone', 'earphone', 'music', 'loud', 'quality', 'bass', 'spatial audio', 'surround sound']
}

# Recommendation keywords to detect recommendation intent
RECOMMENDATION_KEYWORDS = [
    "recommend", "recommendation", "suggested", "suggest", "suggestions", "best", 
    "top", "great", "excellent", "outstanding", "superior", "preferred", "ideal", 
    "perfect", "suitable", "good", "better", "greatest", "finest", "premier", 
    "leading", "exceptional", "recommended", "popular", "worth", "worthwhile", 
    "valuable", "quality", "impressive", "admirable", "advise", "guidance", "options", 
    "choices", "alternatives", "selection", "pick", "choose", "what should i get", 
    "which one", "which phone", "which device", "looking for", "need a new", 
    "want to buy", "considering", "thinking about", "planning to get"
]

# Brands for brand detection
POPULAR_BRANDS = [
    "samsung", "apple", "iphone", "google", "pixel", "xiaomi", "huawei", "oneplus", 
    "oppo", "vivo", "realme", "sony", "motorola", "nokia", "lg", "htc", 
    "honor", "asus", "lenovo", "poco", "redmi", "nothing", "blackberry"
]

# Common device types and categories
DEVICE_TYPES = [
    "phone", "smartphone", "mobile", "cellphone", "tablet", "ipad", 
    "phablet", "folding phone", "flip phone", "foldable", "portable device"
]

# Comparison keywords
COMPARISON_KEYWORDS = [
    "compare", "comparison", "versus", "vs", "or", "difference", "differences", 
    "better", "worse", "which is better", "prefer", "against", "match up", 
    "side by side", "contrast", "comparable", "alternative to", "compete", 
    "face off", "showdown", "battle", "comparison between", "compared to"
]

# Specification keywords
SPECIFICATION_KEYWORDS = [
    "specs", "specifications", "details", "features", "characteristics", 
    "parameters", "capabilities", "technical details", "components", "hardware", 
    "configuration", "profile", "description", "particulars", "attributes"
]

# Query type detection
QUERY_TYPES = {
    "what": ["what is", "what are", "what does", "what can", "what will", "what should"],
    "how": ["how to", "how do", "how does", "how can", "how will", "how much", "how many"],
    "why": ["why is", "why are", "why does", "why do", "why can't", "why would"],
    "when": ["when will", "when is", "when can", "when does", "when should"],
    "where": ["where is", "where can", "where will", "where to", "where should"],
    "which": ["which is", "which are", "which one", "which device", "which phone"],
    "can": ["can you", "can it", "can the", "can this", "can I"]
}

# Sentiment keywords
SENTIMENT_KEYWORDS = {
    'positive': ['good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic', 'wonderful', 'best', 'perfect', 'love', 'like', 'enjoy'],
    'negative': ['bad', 'terrible', 'awful', 'poor', 'worst', 'dislike', 'hate', 'horrible', 'disappointing', 'disappointed', 'issue', 'problem'],
    'neutral': ['okay', 'fine', 'average', 'mediocre', 'decent', 'acceptable', 'fair', 'sufficient', 'adequate', 'passable']
}

# Additional response templates for more advanced scenarios
ADVANCED_RESPONSES = {
    'gaming': [
        "For gaming phones, I recommend devices with powerful processors, high refresh rate displays, and good cooling systems. Would you like some specific recommendations?",
        "Mobile gaming requires good performance. I can suggest some phones optimized for gaming with excellent processors and displays.",
        "Gaming on mobile devices is best with phones that have powerful GPUs, large batteries, and high refresh rate screens. Would you like some suggestions?"
    ],
    'photography': [
        "For photography enthusiasts, I recommend phones with advanced camera systems, good image processing, and manual controls. Would you like some specific recommendations?",
        "If you're into photography, you'll want a phone with multiple lenses, good low-light performance, and advanced camera features. I can suggest some options.",
        "Photography-focused phones typically have excellent main cameras, ultrawide lenses, and often telephoto or macro capabilities. Would you like some recommendations?"
    ],
    'business': [
        "Business users typically need phones with good security features, long battery life, and reliable performance. Would you like some specific recommendations?",
        "For business use, I'd suggest phones with strong security, good productivity apps, and reliable build quality. I can recommend some options.",
        "Business-oriented phones often feature enhanced security, productivity tools, and long support lifecycles. Would you like some specific recommendations?"
    ],
    'content_creation': [
        "For content creators, I recommend phones with excellent cameras, good microphones, and powerful processors for editing. Would you like some specific suggestions?",
        "Content creation needs vary, but typically you'll want a phone with a great camera system, good screen, and powerful processor for editing. I can suggest some options.",
        "If you're creating content, you'll benefit from a phone with high quality cameras, good audio recording, and enough processing power for editing. Would you like recommendations?"
    ],
    'durability': [
        "For someone who needs a durable phone, I can recommend devices with rugged builds, water resistance, and good drop protection. Would you like some specific suggestions?",
        "Durable phones typically feature reinforced frames, water/dust resistance, and shock-absorbing designs. I can suggest some reliable options.",
        "If durability is important to you, look for phones with high IP ratings for water/dust protection and military-grade drop certification. Would you like some recommendations?"
    ],
    'battery_life': [
        "For exceptional battery life, I can recommend phones with large battery capacity and efficient processors. Would you like some specific suggestions?",
        "If battery life is your priority, look for phones with 5000mAh+ batteries and power-efficient displays. I can suggest some long-lasting options.",
        "Phones with the best battery life typically combine large batteries with optimized software and efficient components. Would you like some recommendations?"
    ],
    'value': [
        "For the best value phones, I recommend devices that offer premium features at mid-range prices. Would you like some specific suggestions?",
        "Value-oriented phones give you the most features and performance for your money. I can suggest some excellent options at different price points.",
        "If you're looking for value, I can recommend phones that offer nearly flagship experiences without the premium price tag. Would you like some suggestions?"
    ]
}

# Usage pattern responses for better understanding user needs
USAGE_PATTERN_RESPONSES = {
    'frequent_traveler': "For frequent travelers, phones with excellent battery life, reliable connectivity, and good cameras are ideal. Would you like some travel-friendly recommendations?",
    'heavy_social_media': "If you use social media heavily, you'll benefit from a phone with a good front camera, excellent display, and solid battery life. Would you like some recommendations?",
    'outdoor_enthusiast': "Outdoor enthusiasts need phones with good durability, reliable battery life, and bright displays visible in sunlight. Would you like some ruggedized recommendations?",
    'elderly_user': "For elderly users, phones with simple interfaces, larger text options, good accessibility features, and clear call quality are ideal. Would you like some recommendations?",
    'music_lover': "Music enthusiasts will appreciate phones with high-quality DACs, good headphone support, excellent speakers, and ample storage. Would you like some audio-focused recommendations?",
    'privacy_focused': "If privacy is a priority, you might prefer phones with dedicated security features, minimal data collection, and regular security updates. Would you like some secure recommendations?",
    'multitasker': "For multitasking, I recommend phones with large RAM, efficient processors, and good screen sizes for running multiple apps. Would you like some high-productivity recommendations?",
    'minimalist': "If you prefer a minimalist approach, there are phones with clean interfaces, essential features, and distraction-reducing capabilities. Would you like some streamlined recommendations?",
    'parent': "For parents, phones with good parental controls, durable builds, and reliable performance are ideal. Would you like some family-friendly recommendations?",
    'student': "Students often need affordable phones with good battery life, decent performance for educational apps, and reliable connectivity. Would you like some student-friendly recommendations?"
}

# Technical question templates for handling specific technical queries
TECHNICAL_QUESTIONS = {
    'processor': "The {device_name}'s processor is a {processor_name}, which {performance_description}. It features {cores} cores with a maximum clock speed of {clock_speed}.",
    'screen_technology': "The {device_name} uses a {screen_type} display technology, which offers {benefits}. This type of screen is known for {characteristics}.",
    'charging_tech': "The {device_name} supports {charging_type} charging at up to {charging_speed}. This means you can charge from {start_percent}% to {end_percent}% in about {charging_time}.",
    'camera_sensor': "The main camera on the {device_name} uses a {sensor_size} {sensor_type} sensor with {megapixels} megapixels. This sensor {sensor_benefits}.",
    'water_resistance': "The {device_name} has an IP{rating} rating, which means it's {protection_description}. This makes it suitable for {suitable_conditions} but not for {unsuitable_conditions}.",
    'os_updates': "The {device_name} is expected to receive {os_updates} years of major OS updates and {security_updates} years of security patches. This means support until approximately {end_date}.",
    'connectivity': "The {device_name} supports {connectivity_standards}, including {specific_standards}. This provides {connectivity_benefits} with theoretical speeds up to {max_speed}.",
    'biometrics': "For biometric security, the {device_name} offers {biometric_methods}. The {primary_method} is particularly {effectiveness} and works well in {good_conditions} but may struggle in {challenging_conditions}."
}

# Troubleshooting responses for helping with device issues
TROUBLESHOOTING_RESPONSES = {
    'battery_drain': [
        "Battery drain can be caused by background apps, screen brightness, or aging batteries. Have you noticed which apps or activities seem to drain the battery fastest?",
        "For battery drain issues, try checking battery usage in settings to identify power-hungry apps, reducing screen brightness, or enabling battery saver mode. Would you like more specific advice?",
        "Unexpected battery drain might be due to a recent app installation, system update, or deteriorating battery health. Let's troubleshoot the most likely causes."
    ],
    'slow_performance': [
        "Slow performance can result from insufficient storage space, too many background apps, or outdated software. Have you checked how much free storage you have?",
        "For performance issues, try clearing app cache, closing background apps, or performing a restart. If problems persist, consider backing up and resetting the device.",
        "Performance slowdowns are often caused by fragmented storage, memory-intensive apps, or resource-heavy background processes. Let's identify what might be affecting your device."
    ],
    'overheating': [
        "Overheating can occur during intensive tasks, charging, or if the device is in direct sunlight. When exactly does your device get hot?",
        "For overheating issues, try removing any case while charging, avoiding direct sunlight, closing demanding apps, or using the device in a cooler environment.",
        "Device overheating is often related to demanding apps like games, video recording, or navigation. It could also indicate a hardware issue if it happens during normal use."
    ],
    'connectivity_issues': [
        "Connectivity problems can be related to network congestion, outdated software, or device settings. Have you tried restarting your router or toggling airplane mode?",
        "For connectivity issues, try toggling Wi-Fi/Bluetooth off and on, forgetting and reconnecting to networks, or updating your device software.",
        "Connection problems might be due to interference from other devices, outdated drivers, or incorrect network settings. Let's try some basic troubleshooting steps."
    ],
    'screen_issues': [
        "Screen issues can range from dead pixels to touch sensitivity problems. Could you describe exactly what you're experiencing with the screen?",
        "For screen problems, try adjusting brightness and touch sensitivity settings, restarting your device, or checking for system updates that might address known display issues.",
        "Display problems might be software-related (fixable with updates or settings) or hardware-related (potentially requiring repair). Let's determine which type you're experiencing."
    ],
    'storage_full': [
        "Storage issues typically come from photos/videos, cached data, or unused apps. Have you checked which category is using the most space?",
        "For storage problems, try clearing app caches, removing unused apps, transferring photos/videos to cloud storage, or deleting downloaded files you no longer need.",
        "When storage is filling up, focus first on temporary files and caches, then on large media files, and finally on apps you rarely use. Would you like specific instructions?"
    ],
    'app_crashes': [
        "App crashes can be caused by bugs, memory issues, or conflicts with other apps. Does this happen with one specific app or multiple apps?",
        "For app crashes, try clearing the app's cache, ensuring the app is updated, restarting your device, or reinstalling the problematic app.",
        "When apps keep crashing, it often indicates either an app-specific issue (resolvable by updating or reinstalling) or a system-level problem (potentially fixable with a software update)."
    ],
    'charging_problems': [
        "Charging issues can stem from cable damage, port contamination, or battery degradation. Have you tried different cables or charging adapters?",
        "For charging problems, check the charging port for lint or debris, try different cables and power sources, or restart your device while connected to power.",
        "Difficulty charging often relates to physical components like cables and ports. However, software issues can sometimes affect charging speed or prevent proper battery recognition."
    ]
}

# Usage scenario templates for understanding specific use cases
USAGE_SCENARIOS = {
    'travel': "For travel use, the {device_name} offers {travel_features} which makes it suitable for {travel_scenarios}. However, you should be aware of {limitations}.",
    'photography': "For photography, the {device_name} excels in {photo_strengths} situations thanks to its {camera_features}. It might not perform as well in {photo_weaknesses} conditions.",
    'gaming': "For gaming, the {device_name} can handle {game_types} well with {performance_details}. You might experience {gaming_limitations} with more demanding titles.",
    'business': "For business use, the {device_name} offers {business_features} and {security_aspects}, making it suitable for {business_scenarios}. Consider {business_considerations} for your specific needs.",
    'content_creation': "For content creation, the {device_name} provides {creator_features} which enables {creation_capabilities}. You might find {creation_limitations} for more professional work.",
    'everyday': "For everyday use, the {device_name} offers a {user_experience} experience with {highlight_features}. Most users especially appreciate its {popular_aspects}.",
    'student': "For students, the {device_name} provides {student_benefits} at a {value_proposition}. Its {key_features} are particularly useful for {study_scenarios}."
}

# Enhanced comparison templates for differentiating between devices
COMPARISON_TEMPLATES = {
    'general': "Comparing the {device1} and {device2}, the {device1} offers {device1_advantages} while the {device2} provides {device2_advantages}. Their key differences are in {difference_areas}.",
    'camera': "Camera-wise, the {device1} excels in {device1_photo_strengths} with its {device1_camera_specs}, while the {device2} performs better in {device2_photo_strengths} thanks to {device2_camera_specs}.",
    'performance': "Performance-wise, the {device1} with its {device1_processor} {performance_comparison} the {device2} with its {device2_processor}. This difference is most noticeable when {usage_scenario}.",
    'battery': "For battery life, the {device1} with its {device1_battery_size}mAh battery {battery_comparison} the {device2} with its {device2_battery_size}mAh capacity. This translates to {usage_difference} in typical use.",
    'display': "Display-wise, the {device1}'s {device1_display} {display_comparison} the {device2}'s {device2_display}. You'll notice this difference particularly when {viewing_scenario}.",
    'value': "In terms of value, the {device1} at {device1_price} {value_comparison} the {device2} at {device2_price} considering their respective features and performance.",
    'ecosystem': "Regarding ecosystem, the {device1} with {device1_os} offers {device1_ecosystem_benefits}, while the {device2} with {device2_os} provides {device2_ecosystem_benefits}. Your preference may depend on {ecosystem_considerations}."
}

# Device-specific feature explanations
FEATURE_EXPLANATIONS = {
    'amoled': "AMOLED displays offer perfect blacks, vivid colors, and energy efficiency since each pixel emits its own light and can be turned completely off for true black.",
    'oled': "OLED technology enables perfect blacks and high contrast ratios by allowing each pixel to be turned off completely, unlike LCD which uses backlighting.",
    'lcd': "LCD displays use a backlight behind the pixels, offering consistent brightness and often better visibility in direct sunlight compared to OLED screens.",
    'refresh_rate': "Higher refresh rates (measured in Hz) make scrolling, animations, and gaming look smoother. A 120Hz display refreshes twice as often as a standard 60Hz screen.",
    'gorilla_glass': "Gorilla Glass is a toughened glass designed to provide better protection against drops and scratches compared to standard display glass.",
    'water_resistance': "Water resistance ratings like IP68 indicate protection against dust and water immersion, but don't guarantee waterproofing for all scenarios or over the device's lifetime.",
    'fast_charging': "Fast charging technologies reduce charging time significantly, often providing hours of usage from just minutes of charging, but may generate more heat and affect battery longevity.",
    'wireless_charging': "Wireless charging offers convenience without port wear, but is typically slower than wired charging and may generate more heat during the charging process.",
    'nfc': "NFC enables contactless payments, quick pairing with compatible devices, and interaction with NFC tags for automation.",
    '5g': "5G connectivity offers significantly faster data speeds and lower latency than 4G, but availability varies by region and may impact battery life when active.",
    'esim': "eSIM technology replaces physical SIM cards with an embedded chip, allowing for easier carrier switching and multiple plans without swapping cards.",
    'expandable_storage': "Expandable storage via microSD cards allows you to increase your device's storage capacity, though apps may not always be movable to the external storage.",
    'telephoto_lens': "Telephoto lenses enable optical zoom, allowing you to capture distant subjects without the quality loss associated with digital zoom.",
    'ultrawide_lens': "Ultrawide lenses capture a much broader field of view than standard lenses, ideal for landscapes, architecture, and group photos in tight spaces.",
    'optical_stabilization': "Optical image stabilization physically moves camera components to counteract hand movements, resulting in sharper photos and smoother videos.",
    'vapor_chamber': "Vapor chamber cooling uses phase change cooling technology to draw heat away from processors more efficiently than traditional cooling methods.",
    'under_display_camera': "Under-display cameras are placed beneath the screen, eliminating the need for notches or hole-punches, though image quality may be compromised.",
    'under_display_fingerprint': "Under-display fingerprint sensors allow for seamless authentication without requiring a separate sensor, though they may be slower than dedicated sensors."
}

# Additional keywords for detecting user intents about specific usage patterns
USAGE_PATTERN_KEYWORDS = {
    'frequent_traveler': ['travel', 'traveling', 'traveller', 'trip', 'journey', 'flight', 'flying', 'commute', 'commuting', 'international', 'roaming', 'abroad'],
    'heavy_social_media': ['social media', 'instagram', 'tiktok', 'facebook', 'snapchat', 'twitter', 'youtube', 'influencer', 'content creator', 'streaming', 'posting'],
    'outdoor_enthusiast': ['outdoor', 'hiking', 'camping', 'adventure', 'rugged', 'durable', 'sports', 'active', 'extreme', 'waterproof', 'mountain', 'beach'],
    'elderly_user': ['elderly', 'senior', 'older', 'easy to use', 'simple', 'accessible', 'large text', 'hearing aid', 'accessibility', 'basic', 'beginner'],
    'music_lover': ['music', 'audiophile', 'headphones', 'earbuds', 'sound quality', 'speaker', 'audio', 'hi-res', 'hi-fi', 'bass', 'streaming music', 'spotify', 'dac'],
    'privacy_focused': ['privacy', 'secure', 'security', 'encrypted', 'protection', 'tracking', 'data collection', 'anonymity', 'confidential', 'sensitive'],
    'multitasker': ['multitask', 'productivity', 'work', 'efficient', 'multiple apps', 'split screen', 'dual screen', 'notes', 'calendar', 'email', 'busy'],
    'minimalist': ['minimal', 'minimalist', 'simple', 'clean', 'distraction-free', 'focus', 'essential', 'basic', 'digital wellbeing', 'screentime'],
    'parent': ['parent', 'kids', 'family', 'child', 'children', 'parental controls', 'monitoring', 'restrictions', 'safe', 'family sharing', 'location tracking'],
    'student': ['student', 'school', 'college', 'university', 'education', 'study', 'notes', 'textbooks', 'research', 'assignment', 'affordable', 'budget']
}

# Technical scenario keywords for identifying specific technical questions
TECHNICAL_SCENARIO_KEYWORDS = {
    'processor': ['processor', 'cpu', 'chipset', 'soc', 'snapdragon', 'exynos', 'dimensity', 'bionic', 'chip', 'cores', 'clock speed', 'nanometer', 'performance'],
    'screen_technology': ['screen technology', 'display type', 'panel', 'amoled', 'oled', 'lcd', 'ips', 'ltpo', 'refresh rate', 'response time', 'hdr', 'nits', 'brightness'],
    'charging_tech': ['charging technology', 'fast charging', 'quick charge', 'supervooc', 'supercharge', 'power delivery', 'wireless charging', 'reverse charging', 'battery tech'],
    'camera_sensor': ['camera sensor', 'sensor size', 'sony sensor', 'samsung sensor', 'pixel size', 'microns', 'image sensor', 'aperture', 'ois', 'sensor shift'],
    'water_resistance': ['water resistance', 'ip rating', 'ip68', 'ip67', 'waterproof', 'water protected', 'dust resistance', 'submersion', 'water damage'],
    'os_updates': ['os updates', 'software updates', 'android version', 'ios version', 'security patches', 'update policy', 'support lifecycle', 'end of support'],
    'connectivity': ['connectivity', '5g', 'lte', '4g', 'wifi', 'bluetooth', 'nfc', 'ultra wideband', 'uwb', 'modem', 'satellite', 'band support', 'mimo'],
    'biometrics': ['biometrics', 'fingerprint', 'face recognition', 'face id', 'iris scanner', 'under display', 'security', 'authentication', 'unlock']
}

# Troubleshooting scenario keywords for identifying user problems
TROUBLESHOOTING_KEYWORDS = {
    'battery_drain': ['battery drain', 'battery life', 'dies quickly', 'losing battery', 'not lasting', 'discharge', 'battery health', 'power consumption', 'draining fast'],
    'slow_performance': ['slow', 'lag', 'sluggish', 'freezing', 'hanging', 'unresponsive', 'performance issues', 'stuttering', 'not smooth', 'taking long time'],
    'overheating': ['overheating', 'hot', 'temperature', 'warm', 'thermal', 'heat up', 'burning', 'feels hot', 'cooling', 'overheat'],
    'connectivity_issues': ['connectivity issue', 'wifi problem', 'bluetooth problem', 'not connecting', 'dropping connection', 'signal', 'weak connection', 'no internet', 'disconnecting'],
    'screen_issues': ['screen problem', 'display issue', 'touch not working', 'ghost touch', 'dead pixel', 'screen flickering', 'green tint', 'burn-in', 'display damage'],
    'storage_full': ['storage full', 'no space', 'memory full', 'can\'t install', 'insufficient storage', 'running out of space', 'delete files', 'free space', 'low storage'],
    'app_crashes': ['app crashing', 'force close', 'not responding', 'keeps closing', 'app problem', 'application error', 'stopped working', 'crashes', 'restarts'],
    'charging_problems': ['not charging', 'slow charging', 'charging issue', 'won\'t charge', 'stops charging', 'charging port', 'cable problem', 'power issue']
}

# Additional brand characteristics for better brand-specific recommendations
BRAND_CHARACTERISTICS = {
    'samsung': {
        'strengths': ['display quality', 'camera versatility', 'feature-rich software', 'ecosystem integration', 'wide product range'],
        'weaknesses': ['software updates can be slow', 'occasional bloatware', 'higher prices for flagships'],
        'unique_features': ['S Pen support', 'DeX desktop mode', 'Knox security', 'foldable phones'],
        'popular_models': ['Galaxy S series', 'Galaxy A series', 'Galaxy Z Fold/Flip', 'Galaxy Note series (discontinued)']
    },
    'apple': {
        'strengths': ['long software support', 'performance', 'camera consistency', 'ecosystem integration', 'build quality'],
        'weaknesses': ['higher prices', 'limited customization', 'proprietary accessories', 'closed ecosystem'],
        'unique_features': ['Face ID', 'iMessage', 'Apple Pay', 'Continuity features', 'Privacy focus'],
        'popular_models': ['iPhone Pro series', 'iPhone standard series', 'iPhone SE']
    },
    'google': {
        'strengths': ['camera processing', 'clean software', 'fast updates', 'AI features', 'voice assistant'],
        'weaknesses': ['limited availability in some regions', 'battery life on some models', 'hardware issues in past generations'],
        'unique_features': ['computational photography', 'call screening', 'on-device AI', 'clean Android experience'],
        'popular_models': ['Pixel Pro series', 'Pixel standard series', 'Pixel A series']
    },
    'xiaomi': {
        'strengths': ['value for money', 'feature-rich hardware', 'fast charging', 'competitive pricing', 'diverse product lineup'],
        'weaknesses': ['software ads in some regions', 'inconsistent update schedule', 'camera processing can be improved'],
        'unique_features': ['MIUI customizations', 'IR blaster on many models', 'extremely fast charging', 'affordable flagships'],
        'popular_models': ['Redmi Note series', 'Poco series', 'Xiaomi number series', 'Xiaomi Ultra models']
    },
    'oneplus': {
        'strengths': ['clean software', 'fast performance', 'quick charging', 'display quality', 'competitive pricing'],
        'weaknesses': ['camera performance on some models', 'software direction changes', 'increasing prices over time'],
        'unique_features': ['OxygenOS (now merging with ColorOS)', 'alert slider', 'Hasselblad partnership for cameras'],
        'popular_models': ['OnePlus number series', 'OnePlus R series', 'OnePlus Nord series']
    },
    'nothing': {
        'strengths': ['unique design', 'clean software', 'competitive pricing', 'audio quality', 'glyph interface'],
        'weaknesses': ['limited product line', 'new brand with less established track record', 'camera performance'],
        'unique_features': ['transparent design elements', 'glyph interface', 'minimal software', 'distinctive aesthetic'],
        'popular_models': ['Nothing Phone series', 'Nothing Ear series']
    },
    'sony': {
        'strengths': ['display quality', 'audio features', 'camera hardware', 'build quality', 'multimedia focus'],
        'weaknesses': ['higher prices', 'limited availability', 'marketing', 'sometimes lagging in trendy features'],
        'unique_features': ['Alpha camera technology', 'BRAVIA display tech', 'PlayStation integration', '3.5mm headphone jack'],
        'popular_models': ['Xperia 1 series', 'Xperia 5 series', 'Xperia 10 series']
    },
    'motorola': {
        'strengths': ['clean software', 'battery life', 'competitive pricing', 'wide availability', 'reliability'],
        'weaknesses': ['camera performance on budget models', 'software update longevity', 'less premium designs on some models'],
        'unique_features': ['near-stock Android', 'Moto actions', 'wide range of budget to mid-range options'],
        'popular_models': ['Moto G series', 'Moto Edge series', 'Razr foldables']
    }
}

# Device specifications response templates
DEVICE_SPECIFICATIONS_RESPONSES = {
    'intro': "Here are the {specification_type} specifications for {device_name}:",
    'not_found': "I couldn't find the {specification_type} specifications for {device_name}. Would you like to know about other specifications instead?",
    'partial_info': "I have partial information about the {specification_type} specifications for {device_name}:",
    'display': "The {device_name} features a {screen_size} {display_type} display with {resolution} resolution{additional_display_features}.",
    'processor': "The {device_name} is powered by a {processor_name}{processor_details}.",
    'memory': "The {device_name} comes with {ram} RAM and {storage} internal storage{expandable_storage}.",
    'camera': "The {device_name}'s camera system includes a {main_camera} main camera{additional_cameras}. The front camera is {selfie_camera}.",
    'battery': "The {device_name} is equipped with a {battery_capacity} battery{charging_capabilities}.",
    'os': "The {device_name} runs on {os_name}{os_version}{update_info}.",
    'connectivity': "Connectivity options on the {device_name} include {connectivity_options}.",
    'dimensions': "The {device_name} measures {dimensions} and weighs {weight}.",
    'features': "Additional features of the {device_name} include {special_features}.",
    'audio': "The {device_name}'s audio capabilities include {audio_features}.",
    'sensors': "The {device_name} includes the following sensors: {sensors_list}.",
    'water_resistance': "The {device_name} has {water_resistance_rating} water and dust resistance.",
    'materials': "The {device_name} is built with {body_materials}.",
    'security': "Security features on the {device_name} include {security_features}.",
    'network': "The {device_name} supports the following network bands: {network_bands}.",
    'colors': "The {device_name} is available in these colors: {color_options}.",
    'price': "The {device_name} is priced at approximately {price_range} depending on the region and configuration.",
    'release_date': "The {device_name} was released in {release_date}.",
    'comparison_intro': "When comparing the {spec_type} between {device1} and {device2}:",
    'comparison_winner': "The {winning_device} has better {spec_type} specifications with {advantage}.",
    'comparison_similar': "Both devices have similar {spec_type} specifications, with {similarities}.",
    'highlight': "A notable feature of the {device_name}'s {specification_type} is {highlight_feature}.",
    'detailed_specs': "Here are more detailed specifications for the {device_name}'s {specification_type}:\n{detailed_list}",
    'all_specs': "Here's a comprehensive overview of the {device_name}'s specifications:"
}

# Categories of specifications for better organization
SPECIFICATION_CATEGORIES = {
    'display': ['screen size', 'resolution', 'display type', 'refresh rate', 'brightness', 'pixel density', 'aspect ratio', 'color depth', 'hdr support', 'touch sampling rate', 'screen protection'],
    'performance': ['processor', 'cpu', 'chipset', 'gpu', 'benchmark scores', 'antutu', 'geekbench', 'gaming performance', 'thermal management'],
    'memory': ['ram', 'storage', 'expandable storage', 'memory type', 'ufs', 'nvme'],
    'camera': ['main camera', 'ultra wide', 'telephoto', 'macro', 'depth sensor', 'front camera', 'selfie camera', 'video recording', 'camera features', 'night mode', 'portrait', 'optical zoom'],
    'battery': ['battery capacity', 'charging speed', 'wireless charging', 'reverse charging', 'battery life', 'standby time', 'talk time', 'video playback time'],
    'audio': ['speakers', 'headphone jack', 'audio quality', 'dolby atmos', 'stereo speakers', 'hi-res audio', 'microphones'],
    'connectivity': ['5g', '4g', 'wifi', 'bluetooth', 'nfc', 'gps', 'usb type', 'infrared', 'wireless connectivity'],
    'software': ['operating system', 'android version', 'ios version', 'ui skin', 'software features', 'update policy', 'bloatware'],
    'design': ['dimensions', 'weight', 'build material', 'colors', 'waterproof', 'dust resistant', 'ip rating', 'gorilla glass'],
    'security': ['fingerprint', 'face unlock', 'encryption', 'secure folder', 'privacy features'],
    'special_features': ['stylus', 'foldable', 'gaming features', 'desktop mode', 'fast charging', 'unique selling points']
}

# Priority specifications based on device type
SPECIFICATION_PRIORITIES = {
    'flagship': ['processor', 'camera', 'display', 'build quality', 'special features'],
    'mid_range': ['value for money', 'battery life', 'camera', 'performance'],
    'budget': ['price', 'battery life', 'basic performance', 'storage options'],
    'gaming': ['processor', 'gpu', 'cooling', 'refresh rate', 'battery', 'ram'],
    'camera_focused': ['main camera', 'camera features', 'image processing', 'video capabilities'],
    'battery_focused': ['battery capacity', 'fast charging', 'battery life optimization'],
    'business': ['security features', 'productivity tools', 'build quality', 'battery life'],
    'compact': ['size', 'one-handed usage', 'weight', 'pocket friendliness'],
    'foldable': ['folding mechanism', 'durability', 'multi-tasking', 'screen technology']
}

# Templates for device comparisons
DEVICE_COMPARISON_TEMPLATES = {
    'general_comparison': [
        "When comparing the {device1} and {device2}, here's how they stack up:",
        "Here's a comparison between the {device1} and {device2}:",
        "Let me break down the key differences between the {device1} and {device2}:"
    ],
    'specific_comparison': [
        "Comparing the {spec} between {device1} and {device2}: the {device1} has {device1_spec_value}, while the {device2} has {device2_spec_value}.",
        "For {spec}: {device1} offers {device1_spec_value}, whereas {device2} provides {device2_spec_value}.",
        "Looking at {spec}, the {device1} comes with {device1_spec_value}, compared to {device2}'s {device2_spec_value}."
    ],
    'winner_statement': [
        "The {winner} has an edge in {category}.",
        "When it comes to {category}, the {winner} performs better.",
        "For {category}, I'd recommend the {winner}.",
        "The {winner} outperforms in the {category} department."
    ],
    'tie_statement': [
        "Both devices are quite similar when it comes to {category}.",
        "There's not much difference between the two in terms of {category}.",
        "For {category}, both devices offer comparable performance.",
        "The {category} is nearly identical on both devices."
    ],
    'summary': [
        "Overall, the {winner} is better for {use_case}, while the {loser} might be preferable if you prioritize {loser_strength}.",
        "In summary, choose the {winner} if {winner_advantage} matters to you, but consider the {loser} if you value {loser_advantage}.",
        "Bottom line: {winner} excels in {winner_key_points}, while {loser} stands out for {loser_key_points}."
    ]
}

# Responses for handling missing specifications
MISSING_SPECIFICATION_RESPONSES = {
    'not_available': [
        "I couldn't find information about the {spec} for the {device}.",
        "The {spec} details aren't available for the {device} in my database.",
        "I don't have data on the {device}'s {spec}."
    ],
    'suggestion': [
        "You might want to check the manufacturer's website for the most accurate {spec} information.",
        "For detailed {spec} information, I recommend visiting the official {brand} website.",
        "The most up-to-date {spec} details can usually be found on GSMArena or the official {brand} page."
    ],
    'alternative_info': [
        "While I don't have information on {spec}, I can tell you that the {device} {alternative_info}.",
        "I don't have the exact {spec} details, but I can share that this device {alternative_info}.",
        "Though the {spec} information is missing, it's worth noting that the {device} {alternative_info}."
    ]
}

# Templates for device recommendations
RECOMMENDATION_TEMPLATES = {
    'intro': [
        "Based on your requirements, here are some devices you might consider:",
        "I've found some devices that match what you're looking for:",
        "Here are my recommendations based on your preferences:"
    ],
    'budget_statement': [
        "For your budget of around {budget}, these options offer excellent value:",
        "Within the {budget} price range, these devices stand out:",
        "If you're looking to spend about {budget}, consider these options:"
    ],
    'use_case_intro': [
        "For {use_case}, you'll want a device with {key_specs}. Here are some great options:",
        "When it comes to {use_case}, these devices excel with their {key_specs}:",
        "Looking for a phone for {use_case}? These models with {key_specs} should work well:"
    ],
    'single_recommendation': [
        "The {device} would be an excellent choice for you. It features {key_features} and is priced around {price}.",
        "I'd recommend the {device}. With {key_features}, it perfectly matches your needs at approximately {price}.",
        "Consider the {device} - it offers {key_features} and falls within your budget at around {price}."
    ],
    'conclusion': [
        "All of these options provide {common_strength}, but my top pick would be the {top_pick} because {reason}.",
        "While each device has its strengths, the {top_pick} stands out for {reason} and offers the best overall value.",
        "You can't go wrong with any of these, but the {top_pick} edges ahead because {reason}."
    ]
}

# Templates for general device queries
GENERAL_DEVICE_QUERIES = {
    'device_age': [
        "The {device} was released in {release_date}.",
        "The {device} came out in {release_date}.",
        "{device} has been on the market since {release_date}."
    ],
    'device_price': [
        "The {device} is typically priced around {price_range}.",
        "You can expect to pay approximately {price_range} for the {device}.",
        "The current market price for the {device} is about {price_range}."
    ],
    'availability': [
        "The {device} is {availability_status} in {region}.",
        "In {region}, the {device} is {availability_status}.",
        "As for availability, the {device} is {availability_status} in {region}."
    ],
    'upcoming_release': [
        "The {device} is expected to be released in {expected_date}.",
        "According to current information, the {device} should launch around {expected_date}.",
        "The {device} is scheduled for release in {expected_date}."
    ],
    'general_opinion': [
        "The {device} is generally considered {opinion} for {use_case}.",
        "For {use_case}, the {device} is {opinion} according to most reviews.",
        "The {device} is {opinion} for {use_case} according to user feedback."
    ]
}

# Templates for handling user feedback and interaction
USER_INTERACTION_RESPONSES = {
    'clarification_request': [
        "Could you specify which {aspect} you're interested in for the {device}?",
        "I'd be happy to help with that. Which {aspect} of the {device} would you like to know about?",
        "To better assist you, could you tell me which {aspect} of the {device} matters most to you?"
    ],
    'positive_feedback': [
        "I'm glad that was helpful! Is there anything else you'd like to know about mobile devices?",
        "Great! I'm happy I could assist. Any other device questions I can help with?",
        "Excellent! Let me know if you need more information about any other devices or specifications."
    ],
    'negative_feedback': [
        "I apologize for the confusion. Let me try to provide better information about {topic}.",
        "I'm sorry that wasn't what you were looking for. Could you clarify what specific details you need about {topic}?",
        "Thank you for letting me know. Let me improve my response regarding {topic}."
    ],
    'missing_information': [
        "I don't have complete information about {topic} yet. Would you like me to tell you what I do know?",
        "The details about {topic} aren't fully available in my database. I can share what information I do have if that would help.",
        "I have limited information about {topic}. Would you like me to provide what I know and suggest where to find more details?"
    ],
    'follow_up_suggestions': [
        "Based on your interest in {current_topic}, you might also want to know about {related_topic}. Would you like details on that?",
        "Since we're discussing {current_topic}, many users also ask about {related_topic}. Would that be useful for you?",
        "Would you also like information about {related_topic}? It's closely related to {current_topic} and might be relevant to your needs."
    ]
} 