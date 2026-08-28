# Image Analysis Feature for Detection

## Overview
Users can upload images (screenshots of scam messages, emails, or payment requests) and receive a Gemini-powered scam/fraud analysis in a new chatbot conversation.

## Implementation Details

### Technology Used
- **Gemini multimodal analysis** - The backend sends the image directly to Gemini
- A fixed cybersecurity system prompt controls the analysis
- Authenticated users receive a persisted new chat containing the image and response

### How It Works
1. User clicks the "+" button in the Detection page
2. Selects an image file (PNG, JPG, GIF, or WebP)
3. User may crop the image to the relevant area
4. The user must apply a crop before the **Submit Image** button becomes available
5. The cropped image is submitted without a user-written prompt to `/api/chat/image-analysis/`
6. Gemini analyzes the image using the fixed scam/fraud analysis prompt
7. The Detection page shows Gemini's report

### Features
✅ **Image Upload** - Click the "+" button to upload images  
✅ **Live Preview** - See and crop the uploaded image before analysis
✅ **Analysis Status** - Clear status while Gemini evaluates the image
✅ **Validation** - File type and size validation (max 10MB)  
✅ **Error Handling** - Clear error messages for failed OCR or invalid files  
✅ **Direct Image Analysis** - No OCR transcription or user prompt is required
✅ **Remove Image** - Option to remove image and start over  

### File Changes

#### 1. Backend Endpoint
- Added `POST /api/chat/image-analysis/`
- Uses Gemini's multimodal API and persists the resulting chat for authenticated users

#### 2. [`frontend/src/pages/Detection.jsx`](../frontend/src/pages/Detection.jsx)
**New State Variables:**
```javascript
const [selectedImage, setSelectedImage] = useState(null);
const [imagePreview, setImagePreview] = useState(null);
const [isAnalyzingImage, setIsAnalyzingImage] = useState(false);
const fileInputRef = useRef(null);
```

**New Functions:**
- `handleImageSelect()` - Handles image file selection and validation
- `handleCropAndAnalyze()` - Applies the required crop
- `handlePlusButtonClick()` - Triggers file input dialog
- `handleRemoveImage()` - Clears selected image
- Updated `handleNewAnalysis()` - Resets image states

**UI Updates:**
- Image preview and crop component
- Updated placeholder text to mention image upload
- Added disabled states during OCR extraction
- Hidden file input element

#### 3. [`frontend/src/index.css`](../frontend/src/index.css)
**New Styles:**
- `.detect__imagePreview` - Container for image preview
- `.detect__imagePreview-header` - Header with title and remove button
- `.detect__imagePreview-img` - Image display styling
- `.detect__imagePreview-progress` - OCR progress UI
- `.detect__imagePreview-progressBar` - Progress bar container
- `.detect__imagePreview-progressFill` - Animated progress fill
- `.detect__imagePreview-progressText` - Progress percentage text
- `.detect__plus:disabled` - Disabled state for upload button

## Usage

### For Users
1. Go to the Detection page
2. Click the **"+"** button
3. Select an image containing text (screenshot, photo of message, etc.)
4. Click **Analyze Image**
5. Review Gemini's report in the new chatbot conversation

### Supported Image Formats
- PNG
- JPG/JPEG
- GIF
- WebP

### Limitations
- Maximum file size: **10MB**
- Gemini must be configured with `GEMINI_API_KEY` and enabled with `GEMINI_ENABLED`
- Anonymous results are held only in the current session and are not persisted
- Authenticated chat history stores a resized, compressed preview
- Best results with:
  - Clear, high-resolution images
  - Good contrast between text and background
  - Straight/non-rotated text
  - Printed or digital text (not handwritten)

## Example Use Cases
- Screenshot of a suspicious WhatsApp message
- Photo of a phishing email on another device
- Screenshot of a fake website/promo
- Image of a text message scam
- Photo of a physical letter/flyer

## Future Enhancements (Optional)
- Support for multiple languages
- Image preprocessing (brightness, contrast adjustment)
- Support for multiple images at once
- OCR quality score indicator
- Auto-rotation of tilted images

## Technical Notes
- The original upload is sent to the backend and then to Gemini for multimodal analysis
- The backend does not use the OCR pipeline for this feature
- Gemini failures return service-unavailable; the text-only Gemma fallback is not used for images

## Performance
- Small images (<1MB): ~2-5 seconds
- Medium images (1-5MB): ~5-10 seconds  
- Large images (5-10MB): ~10-20 seconds

Analysis time depends on image resolution, network latency, Gemini availability, and service load.

## Security Considerations
- File type validation to prevent non-image uploads
- File size limit to prevent memory issues
- A fixed server-controlled prompt prevents user prompt injection through the request
- Image content is treated as untrusted by the analysis prompt
- Persisted previews are bounded to reduce database growth
