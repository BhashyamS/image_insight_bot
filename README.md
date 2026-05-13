# Image Insight Bot
Demo Link: [https://imageinsightbot-jq29agmbspkmvbhzbsg7if.streamlit.app/]

An AI-powered Streamlit prototype that analyzes uploaded images and turns visual content into captions, detected objects, searchable tags, confidence-style scores, and business recommendations.

## Problem
Marketing analytics teams often review product, retail, event, and campaign photos manually. This process is slow and inconsistent. Image Insight Bot automates a first-pass review so teams can quickly understand what is in an image and what actions it suggests.

## Features
- Upload PNG, JPG, or JPEG images
- Generate a caption
- Detect visible objects/entities
- Classify the image as Product, Lifestyle, Event, Retail, Social Content, or Other
- Display confidence-style scores
- Show estimated object bounding boxes for explainability
- Generate marketing insights and recommendations
- Support multiple image uploads with a comparison summary
- Export analysis as JSON

## Architecture

```text
Image Upload → Streamlit UI → Gemini Vision API → Structured JSON → Dashboard + JSON Export
```

## Model / API
This app uses Google AI Studio / Gemini API through the `google-genai` Python SDK. The default model is `gemini-2.5-flash`, which supports image understanding and is suitable for a lightweight demo.

## Confidence scoring
The confidence score is a visual clarity score, not a hidden model probability. The prompt asks Gemini to estimate confidence based on how clear and visible the image evidence is.

## Example output

```json
{
  "caption": "A retail display featuring packaged wellness products on a shelf.",
  "image_type": "Retail",
  "detected_objects": [
    {"label": "product packaging", "confidence": 92, "evidence": "multiple boxed items visible"},
    {"label": "store shelf", "confidence": 89, "evidence": "products arranged on shelving"}
  ],
  "marketing_insights": [
    {
      "insight": "The image is useful for shelf visibility analysis.",
      "why_it_matters": "Retail teams can evaluate product placement and packaging clarity."
    }
  ],
  "campaign_recommendations": [
    {
      "team": "Marketing",
      "recommendation": "Use similar imagery for retail availability or product education content."
    }
  ],
  "overall_confidence": 88
}
```

## Future improvements
- Add a dedicated object detection model for more precise boxes
- Save analysis history
- Build a trend dashboard across multiple campaign images
- Add Google Drive or Dropbox upload
- Add brand visibility and campaign quality scoring
