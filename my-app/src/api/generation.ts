import { apiClient } from './client';

export interface GenerationRequest {
  text?: string;
  product_name?: string;
  product_category?: string;
  target_audience?: string;
  user_description?: string;
  target_language?: string;
  image?: string;
  images?: string[];
}

export interface GenerationResponse {
  description: string;
}

export interface SaveGenerationRequest {
  product_name: string;
  product_category: string;
  target_audience: string;
  user_description: string;
  target_language: string;
  final_description: string;
  image_urls?: string[];
}

export interface SaveGenerationResponse {
  message: string;
  id: string;
  updated: boolean;
}

export interface GenerationHistory {
  id: string;
  product_name: string;
  product_category: string;
  target_audience: string;
  user_description: string;
  target_language: string;
  image_urls: string[];
  final_description: string;
  created_at: string;
  updated_at: string;
}

export interface TranslateRequest {
  description: string;
  languages: string[];
}

export interface TranslateResponse {
  translations: Record<string, string>;
}

export const generationApi = {
  generate: async (request: GenerationRequest): Promise<GenerationResponse> => {
    const response = await apiClient.post<GenerationResponse>('/api/generate-description', request);
    return response.data;
  },

  save: async (request: SaveGenerationRequest): Promise<SaveGenerationResponse> => {
    const response = await apiClient.post<SaveGenerationResponse>('/api/generations/save', request);
    return response.data;
  },

  getHistory: async (): Promise<GenerationHistory[]> => {
    const response = await apiClient.get<{ generations: GenerationHistory[] }>('/api/generations');
    return response.data.generations;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/generations/${id}`);
  },

  translate: async (request: TranslateRequest): Promise<TranslateResponse> => {
    const response = await apiClient.post<TranslateResponse>('/api/translate-description', request);
    return response.data;
  },
};



