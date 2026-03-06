# Image OCR Feature for Detection

## Overview
Added simple image-to-text extraction feature that allows users to upload images (screenshots of scam messages, emails, etc.) and automatically extract text for scam detection analysis.

## Implementation Details

### Technology Used
- **Tesseract.js** - Client-side OCR (Optical Character Recognition) library
- No backend changes required
- Works entirely in the browser

### How It Works
1. User clicks the "+" button in the Detection page
2. Selects an image file (PNG, JPG, etc.)
3. Tesseract.js extracts text from the image
4. Extracted text is automatically populated into the textarea
5. User can review/edit the text before clicking "Detect"
6. The existing scam detection pipeline processes the text normally

### Features
✅ **Image Upload** - Click the "+" button to upload images  
✅ **Live Preview** - See the uploaded image before OCR  
✅ **Progress Tracking** - Visual progress bar during text extraction  
✅ **Validation** - File type and size validation (max 10MB)  
✅ **Error Handling** - Clear error messages for failed OCR or invalid files  
✅ **Editable Text** - Review and edit extracted text before detection  
✅ **Remove Image** - Option to remove image and start over  

### File Changes

#### 1. Frontend Dependencies
- Added `tesseract.js` package

#### 2. [`frontend/src/pages/Detection.jsx`](../frontend/src/pages/Detection.jsx)
**New State Variables:**
```javascript
const [selectedImage, setSelectedImage] = useState(null);
const [imagePreview, setImagePreview] = useState(null);
const [isExtractingText, setIsExtractingText] = useState(false);
const [ocrProgress, setOcrProgress] = useState(0);
const fileInputRef = useRef(null);
```

**New Functions:**
- `handleImageSelect()` - Handles image file selection and validation
- `extractTextFromImage()` - Performs OCR using Tesseract.js
- `handlePlusButtonClick()` - Triggers file input dialog
- `handleRemoveImage()` - Clears selected image
- Updated `handleNewAnalysis()` - Resets image states

**UI Updates:**
- Image preview component with progress bar
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
2. Click the **"+"** button (now shows ⏳ during extraction)
3. Select an image containing text (screenshot, photo of message, etc.)
4. Wait for OCR to extract text (progress shown)
5. Review the extracted text in the textarea
6. Edit if needed
7. Click "Detect" to analyze

### Supported Image Formats
- PNG
- JPG/JPEG
- GIF
- WebP
- BMP

### Limitations
- Maximum file size: **10MB**
- Language: **English** (can be extended to other languages)
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
- OCR happens client-side (no server load)
- Original image is NOT sent to the server
- Only extracted text goes through the detection API
- Privacy-friendly: images stay in the browser
- No additional backend infrastructure required

## Performance
- Small images (<1MB): ~2-5 seconds
- Medium images (1-5MB): ~5-10 seconds  
- Large images (5-10MB): ~10-20 seconds

OCR speed depends on:
- Image resolution
- Amount of text
- User's device performance

## Security Considerations
- File type validation to prevent non-image uploads
- File size limit to prevent memory issues
- Client-side processing (images don't leave the user's device)
- Same text validation as manual input
- No image data stored or transmitted to backend
