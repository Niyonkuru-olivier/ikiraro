# UMUHUZA Chatbot Training Guide

## Overview
This guide provides instructions for training the UMUHUZA chatbot to respond accurately to agriculture-related questions using Botpress.

## Knowledge Base
A comprehensive knowledge base has been created in `chatbot_knowledge_base.json` containing all agriculture information from the UMUHUZA platform.

## Training Steps

### Step 1: Access Botpress Dashboard
1. Go to https://studio.botpress.cloud
2. Log in with your Botpress account
3. Select the bot with ID: `f5a1ef00-3dd2-4a3e-b8b9-0ba70c5f6d37`

### Step 2: Import Knowledge Base
1. Navigate to **Knowledge** or **QnA** section in Botpress
2. Click **Import** or **Add Knowledge**
3. Upload the `chatbot_knowledge_base.json` file
4. Alternatively, manually add the content from the knowledge base

### Step 3: Create Intents and Responses

#### Intent: `greeting`
**User says:**
- "Hello"
- "Hi"
- "Good morning"
- "Hey"

**Bot responds:**
"Hello! Welcome to UMUHUZA - Revolutionizing Agriculture Through Collaborative Artificial Intelligence. How can I help you today? I can assist you with information about our services, weather forecasts, irrigation systems, market prices, agricultural inputs, and more!"

#### Intent: `ask_about_services`
**User says:**
- "What services do you offer?"
- "Tell me about your services"
- "What can you help me with?"
- "What services are available?"

**Bot responds:**
"UMUHUZA offers several agricultural services:

1. **Extension Services**: 
   - Crop Consultancy: Expert guidance on crop management, pest control, and improving maize yields
   - Irrigation Solutions: Help with installing and maintaining modern irrigation systems

2. **Irrigation Technology**: Modern irrigation systems including drip and sprinkler irrigation

3. **Weather Forecasting**: Real-time weather data to help with crop planning and irrigation scheduling

4. **Market Price Information**: Access to maize market prices database with historical trends

5. **Input Information**: Support with agricultural inputs including seeds, fertilizers, pesticides, and irrigation tools

Would you like more details about any specific service?"

#### Intent: `ask_about_weather`
**User says:**
- "How can I get weather forecasts?"
- "Tell me about weather forecasting"
- "What weather information is available?"
- "Weather forecast"

**Bot responds:**
"Our weather forecasting service provides several benefits:

- **Optimizing Irrigation Scheduling**: Adjust irrigation based on rain forecasts to conserve water
- **Crop Planning**: Determine best planting times based on weather patterns
- **Yield Prediction**: Use weather data to predict crop yields
- **Risk Management**: Weather-indexed insurance products

Farmers can access weather forecasts through their dashboard, which displays daily temperature and rainfall data using the Open-Meteo API. This helps in planning irrigation schedules and crop management activities.

Would you like to know more about how to use weather data for farming?"

#### Intent: `ask_about_irrigation`
**User says:**
- "Tell me about irrigation"
- "What irrigation systems do you offer?"
- "How does irrigation work?"
- "Irrigation help"

**Bot responds:**
"UMUHUZA provides comprehensive irrigation solutions for maize farming in Rwanda:

**Irrigation Systems Available:**
- Drip irrigation (most popular for maize - water efficient)
- Sprinkler irrigation
- Surface irrigation

**What We Offer:**
- Affordable drip and sprinkler irrigation systems
- Training on water management and irrigation techniques
- Collaboration with water management authorities for steady water supply
- Soil sensors to monitor moisture levels

**Benefits:**
- Efficient water use
- Direct water delivery to plant roots
- Improved crop yields
- Water conservation

Irrigation is critical for maize farming, especially in regions with inconsistent rainfall. Would you like information about installing an irrigation system?"

#### Intent: `ask_about_market_prices`
**User says:**
- "What are current market prices?"
- "Tell me about market prices"
- "Market price information"
- "How much does maize cost?"

**Bot responds:**
"Our Market Price service provides:

- Searchable database of maize market prices
- Historical price data from 2020-2024
- Price trends and charts
- Regional price information

This helps farmers make informed decisions about when to sell their crops and understand market trends. You can access market prices through your dashboard or visit our Market Price page.

Would you like to know how to access the market price database?"

#### Intent: `ask_about_inputs`
**User says:**
- "How do I order agricultural inputs?"
- "Tell me about inputs"
- "What inputs are available?"
- "Agricultural inputs"

**Bot responds:**
"UMUHUZA provides comprehensive input management:

**Available Inputs:**
- Seeds (quality varieties)
- Fertilizers (NPK based on soil needs)
- Pesticides
- Irrigation tools

**Features:**
- **Personalized Recommendations**: Best inputs for your specific crops and soil types
- **Nutrient Guidance**: Fertilizer recommendations based on soil tests
- **Supplier Partnerships**: Quality and affordable inputs
- **Bulk Purchasing**: Group buying to lower costs
- **Training Programs**: Workshops on best practices

**How to Order:**
1. Log in to your dashboard
2. View agro-dealer inventory
3. Place orders for needed inputs
4. Track orders through 'My Orders' section

Would you like help with specific input recommendations?"

#### Intent: `ask_about_umuhuza`
**User says:**
- "What is UMUHUZA?"
- "Tell me about UMUHUZA"
- "Who are you?"
- "What does UMUHUZA do?"

**Bot responds:**
"UMUHUZA is an agricultural platform revolutionizing agriculture through collaborative artificial intelligence. 

**Our Mission:**
To be the bridge between farmers and all other parties involved in the agriculture sector. We provide farmers with access to information, resources, and support to improve productivity, sustainability, and overall success.

**Our Vision:**
A future where collaborative intelligence is at the heart of agriculture, connecting farmers, agro-dealers, researchers, processors, investors, customers, and policymakers.

**Founded:** 2025 by Olivier Niyonkuru and Ashula Ishimwe

**Location:** Rwanda

**What We Do:**
- Connect all stakeholders in agriculture
- Provide real-time weather and market information
- Offer extension services and training
- Facilitate input ordering and crop sales
- Support sustainable farming practices

Would you like to know more about any specific aspect of our platform?"

#### Intent: `ask_about_sustainable_farming`
**User says:**
- "Tell me about sustainable farming"
- "Sustainable practices"
- "How to farm sustainably?"

**Bot responds:**
"Sustainable farming practices are at the core of UMUHUZA's agricultural initiatives:

**Practices We Promote:**
- Use of organic fertilizers
- Water conservation through efficient irrigation
- Soil health monitoring and improvement
- Crop rotation and diversification
- Integrated pest management
- Resource-efficient technologies

**Benefits:**
- Minimizes environmental impact
- Conserves natural resources
- Improves soil health
- Ensures long-term agricultural productivity
- Reduces dependency on chemical inputs

We provide training and resources to help farmers implement sustainable practices. Would you like information about specific sustainable farming techniques?"

#### Intent: `ask_about_maize_farming`
**User says:**
- "Tell me about maize farming"
- "How to grow maize?"
- "Maize farming tips"
- "Best practices for maize"

**Bot responds:**
"Here are best practices for maize farming in Rwanda:

**Crop Management:**
- Use weather forecasts to plan planting and irrigation schedules
- Apply fertilizers based on soil test results and crop requirements
- Implement drip irrigation for water efficiency
- Monitor soil moisture and nutrient levels using sensors

**Key Inputs:**
- Quality seeds
- Balanced fertilizers (NPK)
- Pesticides for pest control
- Irrigation tools

**Tips:**
- Plan irrigation based on weather forecasts
- Use personalized input recommendations
- Track market prices to optimize harvest timing
- Practice sustainable farming with organic fertilizers
- Collaborate with agro-dealers for quality inputs

UMUHUZA provides expert consultancy on crop management, pest control, and improving maize yields. Would you like specific advice for your farm?"

#### Intent: `ask_about_contact`
**User says:**
- "How can I contact you?"
- "Contact information"
- "Email address"
- "Where are you located?"

**Bot responds:**
"You can contact UMUHUZA through:

**Email:** UMUHUZA@gmail.com

**Social Media:**
- Facebook: facebook.com/ikiraro
- Twitter: @ProjectIkiraro
- Instagram: @ikiraro
- LinkedIn: project-ikiraro-platform
- YouTube: @ProjectIkiraro

**Location:** Rwanda

You can also use the Contact Us page on our website to send us a message directly. We're here to help with any questions about agriculture, our services, or the platform!"

#### Intent: `ask_about_dashboard`
**User says:**
- "What can I do in the dashboard?"
- "Dashboard features"
- "What's in my dashboard?"

**Bot responds:**
"The UMUHUZA dashboard provides farmers with:

1. **Weather Forecast**: Daily temperature and rainfall data
2. **Market Prices**: Recent prices for common commodities
3. **Agro-Dealer Inventory**: View and order inputs (fertilizers, seeds)
4. **My Orders**: Track orders and delivery status
5. **Publish Crops**: List available harvests for sale to processors
6. **Farming Tips**: Contextual advice from weather, market, and sustainability data

To access your dashboard, log in with your account. Don't have an account? You can create one easily!

Would you like help with any specific dashboard feature?"

### Step 4: Configure NLU (Natural Language Understanding)

1. Go to **NLU** section in Botpress
2. Enable **Entity Recognition** for:
   - Services (extension, irrigation, weather, market, inputs)
   - Crops (maize, etc.)
   - Locations (Rwanda, regions)
   - Inputs (seeds, fertilizers, pesticides)

### Step 5: Add Context Variables

Add these context variables to help the bot understand user context:
- `user_role` (farmer, agro-dealer, processor, researcher)
- `user_location` (Rwanda region)
- `crop_type` (maize, etc.)

### Step 6: Create Flows

Create conversation flows for:
1. Service inquiry flow
2. Weather information flow
3. Irrigation consultation flow
4. Market price inquiry flow
5. Input ordering flow
6. General agriculture Q&A flow

### Step 7: Test and Refine

1. Use the **Test Chat** feature in Botpress
2. Test common questions from the intents above
3. Refine responses based on accuracy
4. Add more training examples for better understanding

## Important Notes

- The chatbot should always be helpful and friendly
- If the bot doesn't know an answer, it should direct users to contact support
- Always provide actionable information
- Reference specific pages/services when relevant
- Use the system's color scheme (green #4CAF50) in responses when possible

## Maintenance

- Regularly update the knowledge base with new information
- Monitor user questions and add new intents as needed
- Review and improve responses based on user feedback
- Keep information current with platform updates

