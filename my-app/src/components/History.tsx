import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { generationApi } from '../api/generation';
import type { GenerationHistory } from '../api/generation';
import { Navbar } from './Navbar';
import './History.css';

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

export const History = () => {
  const { isAuthenticated } = useAuth();
  const [generations, setGenerations] = useState<GenerationHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<GenerationHistory>>({});
  const [regenerating, setRegenerating] = useState(false);
  const [translatingId, setTranslatingId] = useState<string | null>(null);
  const [languageInputs, setLanguageInputs] = useState<Record<string, string[]>>({});
  const [translations, setTranslations] = useState<Record<string, Record<string, string>>>({});
  const [translating, setTranslating] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      loadHistory();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const data = await generationApi.getHistory();
      setGenerations(data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Description copied to clipboard!');
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this generation?')) {
      return;
    }

    try {
      await generationApi.delete(id);
      setGenerations((prev) => prev.filter((gen) => gen.id !== id));
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to delete generation');
    }
  };

  const handleEdit = (gen: GenerationHistory) => {
    setEditingId(gen.id);
    setEditForm({
      product_category: gen.product_category,
      target_audience: gen.target_audience,
      user_description: gen.user_description,
      target_language: gen.target_language,
    });
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditForm({});
  };

  const handleRegenerate = async (gen: GenerationHistory) => {
    setRegenerating(true);
    setError('');

    try {
      const response = await generationApi.generate({
        product_name: gen.product_name,
        product_category: editForm.product_category || gen.product_category,
        target_audience: editForm.target_audience || gen.target_audience,
        user_description: editForm.user_description || gen.user_description,
        target_language: editForm.target_language || gen.target_language,
      });

      // Update the form with new description
      setEditForm((prev) => ({ ...prev, final_description: response.description }));
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to regenerate description');
    } finally {
      setRegenerating(false);
    }
  };

  const handleSaveUpdate = async (gen: GenerationHistory) => {
    if (!editForm.final_description) {
      setError('Please regenerate the description first');
      return;
    }

    try {
      await generationApi.save({
        product_name: gen.product_name, // Constant
        product_category: editForm.product_category || gen.product_category,
        target_audience: editForm.target_audience || gen.target_audience,
        user_description: editForm.user_description || gen.user_description,
        target_language: editForm.target_language || gen.target_language,
        final_description: editForm.final_description,
        image_urls: gen.image_urls || [],
      });

      // Reload history to show updated data
      await loadHistory();
      setEditingId(null);
      setEditForm({});
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update generation');
    }
  };

  const handleTranslate = async (gen: GenerationHistory) => {
    const langs = (languageInputs[gen.id] || [])
      .map((lang) => lang.trim())
      .filter((lang) => lang.length > 0);
    
    if (langs.length === 0) {
      setError('Please enter at least one language');
      return;
    }

    if (langs.length > 3) {
      setError('Maximum 3 languages allowed');
      return;
    }

    setTranslating(true);
    setError('');

    try {
      const response = await generationApi.translate({
        description: gen.final_description,
        languages: langs,
      });

      setTranslations((prev) => ({
        ...prev,
        [gen.id]: response.translations,
      }));
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to translate description');
    } finally {
      setTranslating(false);
    }
  };

  const handleLanguageInputChange = (genId: string, index: number, value: string) => {
    setLanguageInputs((prev) => {
      const current = prev[genId] || ['', '', ''];
      const updated = [...current];
      updated[index] = value;
      return { ...prev, [genId]: updated };
    });
  };

  const addLanguageInput = (genId: string) => {
    setLanguageInputs((prev) => {
      const current = prev[genId] || [];
      if (current.length < 3) {
        return { ...prev, [genId]: [...current, ''] };
      }
      return prev;
    });
  };

  const removeLanguageInput = (genId: string, index: number) => {
    setLanguageInputs((prev) => {
      const current = prev[genId] || [];
      const updated = current.filter((_, i) => i !== index);
      return { ...prev, [genId]: updated };
    });
  };

  const toggleTranslationPanel = (genId: string) => {
    if (translatingId === genId) {
      setTranslatingId(null);
    } else {
      setTranslatingId(genId);
      if (!languageInputs[genId]) {
        setLanguageInputs((prev) => ({ ...prev, [genId]: [''] }));
      }
    }
  };

  if (!isAuthenticated) {
    return (
      <>
        <Navbar />
        <div className="history-container">
          <div className="history-message">
            <h2>Please login to view your generation history</h2>
            <Link to="/login" className="login-link">Login here</Link>
          </div>
        </div>
      </>
    );
  }

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="history-container">
          <div className="history-message">Loading...</div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Navbar />
        <div className="history-container">
          <div className="error-message">{error}</div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="history-container">
      <div className="history-header">
        <h1>Generation History</h1>
        <button onClick={loadHistory} className="refresh-button">
          Refresh
        </button>
      </div>

      {generations.length === 0 ? (
        <div className="history-message">
          <p>No generations found. Start generating descriptions to see them here!</p>
        </div>
      ) : (
        <div className="history-list">
          {generations.map((gen) => (
            <div key={gen.id} className="history-item">
              <div className="history-item-header">
                <h3>{gen.product_name}</h3>
                <div className="history-item-actions">
                  <span className="history-date">
                    {new Date(gen.created_at).toLocaleDateString()}
                  </span>
                  {editingId !== gen.id ? (
                    <>
                      <button
                        onClick={() => handleEdit(gen)}
                        className="edit-button"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(gen.id)}
                        className="delete-button"
                      >
                        Delete
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => handleCancelEdit()}
                        className="cancel-button"
                      >
                        Cancel
                      </button>
                    </>
                  )}
                </div>
              </div>

              {editingId === gen.id ? (
                <div className="edit-form">
                  <div className="form-group">
                    <label>Product Category *</label>
                    <select
                      value={editForm.product_category || gen.product_category}
                      onChange={(e) =>
                        setEditForm((prev) => ({ ...prev, product_category: e.target.value }))
                      }
                      className="form-select"
                    >
                      {productTypes.map((type) => (
                        <option key={type} value={type}>
                          {type}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Target Audience *</label>
                    <select
                      value={editForm.target_audience || gen.target_audience}
                      onChange={(e) =>
                        setEditForm((prev) => ({ ...prev, target_audience: e.target.value }))
                      }
                      className="form-select"
                    >
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
                    <label>Additional Description</label>
                    <textarea
                      value={editForm.user_description || gen.user_description || ''}
                      onChange={(e) =>
                        setEditForm((prev) => ({ ...prev, user_description: e.target.value }))
                      }
                      rows={3}
                    />
                  </div>

                  <div className="form-group">
                    <label>Target Language *</label>
                    <input
                      type="text"
                      value={editForm.target_language || gen.target_language}
                      onChange={(e) =>
                        setEditForm((prev) => ({ ...prev, target_language: e.target.value }))
                      }
                    />
                  </div>

                  <div className="edit-actions">
                    <button
                      onClick={() => handleRegenerate(gen)}
                      disabled={regenerating}
                      className="regenerate-button"
                    >
                      {regenerating ? 'Regenerating...' : 'Regenerate Description'}
                    </button>
                    {editForm.final_description && (
                      <button
                        onClick={() => handleSaveUpdate(gen)}
                        className="save-update-button"
                      >
                        Save Update
                      </button>
                    )}
                  </div>

                  {editForm.final_description && (
                    <div className="regenerated-description">
                      <strong>New Generated Description:</strong>
                      <pre>{editForm.final_description}</pre>
                    </div>
                  )}
                </div>
              ) : (
                <>
                  <div className="history-item-meta">
                    <span className="meta-tag">Category: {gen.product_category}</span>
                    <span className="meta-tag">Audience: {gen.target_audience}</span>
                    <span className="meta-tag">Language: {gen.target_language}</span>
                  </div>
                  {gen.user_description && (
                    <div className="history-user-description">
                      <strong>Your input:</strong> {gen.user_description}
                    </div>
                  )}
                  <div className="history-description">
                    <strong>Generated Description:</strong>
                    <pre>{gen.final_description}</pre>
                    <div className="description-actions">
                      <button
                        onClick={() => handleCopy(gen.final_description)}
                        className="copy-button"
                      >
                        Copy
                      </button>
                      <button
                        onClick={() => toggleTranslationPanel(gen.id)}
                        className="translate-button"
                      >
                        {translatingId === gen.id ? 'Hide Translations' : 'Generate in Other Languages'}
                      </button>
                    </div>
                  </div>

                  {translatingId === gen.id && (
                    <div className="translation-panel">
                      <h4>Enter Languages (Max 3)</h4>
                      <p className="translation-hint">Type the language names you want (e.g., Spanish, French, German)</p>
                      <div className="language-inputs">
                        {(languageInputs[gen.id] || ['']).map((lang, index) => (
                          <div key={index} className="language-input-group">
                            <input
                              type="text"
                              value={lang}
                              onChange={(e) => handleLanguageInputChange(gen.id, index, e.target.value)}
                              placeholder={`Language ${index + 1} (e.g., Spanish, French, German)`}
                              className="language-input"
                            />
                            {(languageInputs[gen.id] || []).length > 1 && (
                              <button
                                type="button"
                                onClick={() => removeLanguageInput(gen.id, index)}
                                className="remove-language-button"
                              >
                                ×
                              </button>
                            )}
                          </div>
                        ))}
                        {(languageInputs[gen.id] || []).length < 3 && (
                          <button
                            type="button"
                            onClick={() => addLanguageInput(gen.id)}
                            className="add-language-button"
                          >
                            + Add Language
                          </button>
                        )}
                      </div>
                      <button
                        onClick={() => handleTranslate(gen)}
                        disabled={translating || (languageInputs[gen.id] || []).every((lang) => !lang.trim())}
                        className="generate-translation-button"
                      >
                        {translating ? 'Translating...' : 'Generate Translations'}
                      </button>

                      {translations[gen.id] && Object.keys(translations[gen.id]).length > 0 && (
                        <div className="translations-display">
                          {Object.entries(translations[gen.id]).map(([lang, text]) => (
                            <div key={lang} className="translation-item">
                              <div className="translation-header">
                                <strong>{lang}</strong>
                                <button
                                  onClick={() => handleCopy(text)}
                                  className="copy-button-small"
                                >
                                  Copy
                                </button>
                              </div>
                              <pre>{text}</pre>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
        </div>
      )}
      </div>
    </>
  );
};

