# VisionIQ — AI-Powered Visual Intelligence Platform

## Live Demo

[VisionIQ Streamlit App](https://imageinsightbot-jq29agmbspkmvbhzbsg7if.streamlit.app/?utm_source=chatgpt.com)

## GitHub Repository

[VisionIQ GitHub Repository](https://github.com/BhashyamS/image_insight_bot.git?utm_source=chatgpt.com)

---

## Overview

VisionIQ is an AI-powered visual intelligence platform designed for marketing, ecommerce, retail, and social media analytics teams. The application uses multimodal AI reasoning to analyze uploaded business images and transform them into executive-ready insights, campaign recommendations, and structured intelligence reports.

The platform combines image understanding, object detection, brand analysis, audience prediction, and marketing-focused analytics to help teams evaluate visual content more efficiently and consistently.

---

## Problem Statement

Marketing and ecommerce teams manually review thousands of campaign, retail, and product images to evaluate:

* product visibility
* brand presence
* campaign effectiveness
* social media readiness
* retail shelf placement
* audience engagement potential

This process is often time-consuming, inconsistent, and difficult to scale.

VisionIQ automates this workflow by using AI-powered visual analysis to generate actionable business insights from uploaded images.

---

## Key Features

### AI-Powered Image Analysis

* Upload PNG, JPG, or JPEG images
* Generate contextual image captions
* Detect visible products, objects, and entities
* Classify image types (Product, Retail, Lifestyle, Event, Social Content, etc.)

### Business Intelligence Dashboard

* Executive-ready visual summaries
* Marketing scorecards and campaign-readiness analysis
* Audience prediction and targeting insights
* Brand visibility and packaging clarity analysis
* Channel-fit recommendations for platforms like Instagram, Ecommerce PDPs, and Retail Audits

### Explainable AI Features

* AI-estimated bounding boxes for detected objects
* Structured JSON outputs for transparency
* Confidence-style scoring based on visual clarity and business relevance

### Analytics & Comparison Tools

* Multi-image comparison dashboard
* Campaign optimization suggestions
* Exportable intelligence reports in JSON format

---

## Architecture

```text
Image Upload
      ↓
Streamlit Frontend
      ↓
Google Gemini Vision API
      ↓
Structured JSON Generation
      ↓
Business Intelligence Dashboard
      ↓
Insights + Recommendations + Export
```

---

## Technology Stack

| Technology               | Purpose                          |
| ------------------------ | -------------------------------- |
| Streamlit                | Interactive dashboard frontend   |
| Google Gemini Vision API | Multimodal image reasoning       |
| Python                   | Core application logic           |
| Plotly                   | Visual analytics and scorecards  |
| Pillow                   | Image processing and annotations |
| Pandas                   | Data formatting and analysis     |

---

## AI Capabilities

VisionIQ uses Google Gemini Vision models through the `google-genai` Python SDK to perform:

* multimodal image understanding
* object and scene analysis
* business-focused reasoning
* audience prediction
* campaign optimization analysis

The default model used is `gemini-2.5-flash`.

---

## Marketing Intelligence Features

The platform generates:

* campaign-readiness scores
* branding clarity analysis
* product visibility scoring
* engagement potential estimates
* social media optimization suggestions
* audience targeting predictions
* business recommendations for marketing teams

---

## Example Output

```json
{
  "caption": "A retail display featuring packaged wellness products on a shelf.",
  "image_type": "Retail",
  "marketing_scores": {
    "product_visibility": 92,
    "branding_clarity": 88,
    "campaign_readiness": 90
  },
  "audience_prediction": {
    "primary_group": "Health-conscious consumers",
    "age_range": "25-40"
  },
  "marketing_insights": [
    {
      "insight": "The image is highly suitable for retail shelf visibility analysis.",
      "why_it_matters": "Marketing teams can evaluate product placement and packaging effectiveness."
    }
  ],
  "campaign_recommendations": [
    {
      "team": "Marketing",
      "recommendation": "Use similar imagery for ecommerce and retail promotional campaigns."
    }
  ]
}
```

---

## Future Enhancements

Planned improvements include:

* OCR and text extraction
* advanced object detection models
* historical campaign trend analysis
* brand sentiment prediction
* cloud storage integrations
* campaign performance forecasting
* AI-powered image search and indexing

---

## Business Applications

VisionIQ can support:

* ecommerce product optimization
* retail shelf audits
* social media campaign analysis
* brand visibility monitoring
* influencer marketing evaluation
* event and sponsorship analytics
* visual content quality assessment

---

## Setup Instructions

### Clone Repository

```bash
git clone https://github.com/BhashyamS/image_insight_bot.git
cd image_insight_bot
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Add Gemini API Key

Create a `.streamlit/secrets.toml` file:

```toml
GEMINI_API_KEY="your_api_key_here"
```

### Run Application

```bash
streamlit run app.py
```

---

## Project Highlights

* Multimodal AI reasoning using Gemini Vision
* Business-focused visual intelligence workflows
* Executive-ready dashboard design
* Explainable AI outputs
* Marketing analytics integration
* Real-time image intelligence generation

---

## Author

**Srija Bhashyam**
AI / Data Analytics / Visual Intelligence Projects
