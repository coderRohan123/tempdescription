import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { generationApi } from '../api/generation';
import { Navbar } from './Navbar';
import './Generation.css';

const productTypes = [
  "Foods & Beverages",
  "Clothing & Apparel",
  "Daily Essentials",
  "Electronics & Gadgets",
  "Beauty & Personal Care",
  "Home & Garden",
  "Sports & Outdoors",
  "Books & Media",
  "Toys & Games",
  "Automotive",
  "Health & Wellness",
  "Pet Supplies",
  "Office Supplies",
  "Baby & Kids",
  "Other"
];

export const Generation = () => {
  const { isAuthenticated } = useAuth();
  const [productName, setProductName] = useState('');
  const [productCategory, setProductCategory] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [userDescription, setUserDescription] = useState('');
  const [targetLanguage, setTargetLanguage] = useState('English');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);
  const [images, setImages] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    if (files.length + images.length > 5) {
      setError('Maximum 5 images allowed');
      return;
    }

    const newImages: File[] = [];

    files.forEach((file) => {
      if (file.type.startsWith('image/')) {
        newImages.push(file);
        const reader = new FileReader();
        reader.onload = (event) => {
          const result = event.target?.result as string;
          setImagePreviews((prev) => [...prev, result]);
        };
        reader.readAsDataURL(file);
      }
    });

    setImages((prev) => [...prev, ...newImages]);
  };

  const removeImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
    setImagePreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const convertImagesToBase64 = async (files: File[]): Promise<string[]> => {
    const promises = files.map((file) => {
      return new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const result = reader.result as string;
          resolve(result);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    });
    return Promise.all(promises);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setDescription('');
    setSaved(false);
    setLoading(true);

    let imageBase64: string[] = [];
    
    try {
      // Convert images to base64 only when needed
      if (images.length > 0) {
        imageBase64 = await convertImagesToBase64(images);
      }

      const response = await generationApi.generate({
        product_name: productName,
        product_category: productCategory,
        target_audience: targetAudience,
        user_description: userDescription,
        target_language: targetLanguage,
        images: imageBase64,
      });

      // Show description immediately for both guests and logged-in users
      setDescription(response.description);
      setSaved(false);
      
      // Clear image buffers after successful generation to free memory
      setImages([]);
      setImagePreviews([]);
      // Clear base64 data
      imageBase64 = [];
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to generate description. Please try again.');
    } finally {
      setLoading(false);
      // Ensure cleanup even on error
      imageBase64 = [];
    }
  };

  const handleCopy = () => {
    if (description) {
      navigator.clipboard.writeText(description);
      alert('Description copied to clipboard!');
    }
  };

  const handleSave = async () => {
    if (!isAuthenticated) return;
    
    if (!description) {
      setError('No description to save. Please generate a description first.');
      return;
    }

    setSaving(true);
    setError('');

    try {
      await generationApi.save({
        product_name: productName,
        product_category: productCategory,
        target_audience: targetAudience,
        user_description: userDescription,
        target_language: targetLanguage,
        final_description: description,
        image_urls: [], // In future, you can store image URLs here
      });

      setSaved(true);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to save description. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Navbar />
      <div className="generation-container">
        <div className="hero-section">
          <div className="hero-content">
            <h1 className="hero-title">
              Create Stunning Product Descriptions
              <span className="hero-accent"> Instantly</span>
            </h1>
            <p className="hero-subtitle">
              Transform your product ideas into compelling, SEO-friendly descriptions with AI-powered precision. 
              Perfect for e-commerce, marketplaces, and online stores.
            </p>
            <div className="hero-features">
              <div className="feature-item">
                <span className="feature-icon">🚀</span>
                <span>AI-Powered</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">⚡</span>
                <span>Lightning Fast</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🌍</span>
                <span>Multi-Language</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">💼</span>
                <span>Professional</span>
              </div>
            </div>
            {!isAuthenticated && (
              <p className="guest-notice">
                <Link to="/login">Login</Link> or <Link to="/register">Register</Link> to save your generation history
              </p>
            )}
          </div>
        </div>

      <div className="generation-content">
        <div className="generation-form-container">
          <form onSubmit={handleSubmit} className="generation-form">
            <div className="form-group">
              <label htmlFor="productName">Product Name *</label>
              <input
                id="productName"
                type="text"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                required
                placeholder="e.g., Wireless Bluetooth Headphones"
              />
            </div>

            <div className="form-group">
              <label htmlFor="productCategory">Product Category *</label>
              <select
                id="productCategory"
                value={productCategory}
                onChange={(e) => setProductCategory(e.target.value)}
                required
                className="form-select"
              >
                <option value="">Select category</option>
                {productTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="targetAudience">Target Audience *</label>
              <select
                id="targetAudience"
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
                required
                className="form-select"
              >
                <option value="">Select target audience</option>
                <option value="kids">Kids (Ages 3-12)</option>
                <option value="teens">Teens (Ages 13-19)</option>
                <option value="young-adults">Young Adults (Ages 20-35)</option>
                <option value="adults">Adults (Ages 36-59)</option>
                <option value="seniors">Seniors (Ages 60+)</option>
                <option value="all">All Ages</option>
                <option value="newborns">Newborns (0-12 months)</option>
                <option value="toddlers">Toddlers (1-3 years)</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="userDescription">Additional Description (Optional)</label>
              <textarea
                id="userDescription"
                value={userDescription}
                onChange={(e) => setUserDescription(e.target.value)}
                rows={4}
                placeholder="Add any additional details about the product..."
              />
            </div>

            <div className="form-group">
              <label htmlFor="targetLanguage">Target Language *</label>
              <input
                id="targetLanguage"
                type="text"
                value={targetLanguage}
                onChange={(e) => setTargetLanguage(e.target.value)}
                required
                placeholder="e.g., English, Spanish, French, German, etc."
              />
            </div>

            <div className="form-group">
              <label htmlFor="images">Product Images (Max 5)</label>
              <input
                id="images"
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageChange}
                className="file-input"
              />
              {images.length > 0 && (
                <div className="image-preview-container">
                  {imagePreviews.map((preview, index) => (
                    <div key={index} className="image-preview-item">
                      <img src={preview} alt={`Preview ${index + 1}`} />
                      <button
                        type="button"
                        onClick={() => removeImage(index)}
                        className="remove-image-button"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
              <p className="image-hint">
                {images.length}/5 images selected. You can upload up to 5 images.
              </p>
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" disabled={loading} className="generate-button">
              {loading ? 'Generating...' : 'Generate Description'}
            </button>

            {isAuthenticated && description && (
              <button
                type="button"
                onClick={handleSave}
                disabled={saving || saved || !description}
                className="save-button"
              >
                {saving ? 'Saving...' : saved ? 'Saved ✓' : 'Save to History'}
              </button>
            )}
          </form>
        </div>

      </div>
      
      {/* Render result below the form */}
      {description && (
        <div className="result-container result-below-form">
          <div className="result-header">
            <h2>Generated Description</h2>
            {saved && isAuthenticated && (
              <span className="saved-badge">✓ Saved to history</span>
            )}
            {!saved && isAuthenticated && (
              <span className="pending-badge">⚠ Not saved yet</span>
            )}
            <button onClick={handleCopy} className="copy-button">
              Copy
            </button>
          </div>
          <div className="result-content">
            <pre>{description}</pre>
          </div>
        </div>
      )}
      </div>
    </>
  );
};

