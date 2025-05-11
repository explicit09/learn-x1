import apiClient from './client';

export interface AIInteractionCreate {
  question: string;
  context_type: string; // 'course', 'material', 'quiz'
  context_id: string;
}

export interface AIInteraction {
  id: string;
  user_id: string;
  question: string;
  answer: string;
  context_type: string;
  context_id: string;
  created_at: string;
}

export interface AISearchQuery {
  query: string;
  context_type: string; // 'course', 'material'
  context_id: string;
  limit?: number;
}

export interface AISearchResult {
  results: Array<{
    id: string;
    content: string;
    similarity: number;
    source_id: string;
    source_type: string;
    metadata: Record<string, any>;
  }>;
}

export interface AIQuizGenerationRequest {
  material_id: string;
  num_questions: number;
  difficulty: string; // 'easy', 'medium', 'hard'
}

export interface AIExplanationRequest {
  content_id: string;
  learning_style?: string; // 'visual', 'auditory', 'reading', 'kinesthetic'
  difficulty_level?: string; // 'beginner', 'intermediate', 'advanced'
}

export interface LearningStyleUpdate {
  visual_score: number; // 1-10
  auditory_score: number; // 1-10
  reading_score: number; // 1-10
  kinesthetic_score: number; // 1-10
}

const aiService = {
  async getLearningStyle() {
    const response = await apiClient.get('/ai/learning-style');
    return response.data;
  },

  async updateLearningStyle(data: LearningStyleUpdate) {
    const response = await apiClient.put('/ai/learning-style', data);
    return response.data;
  },

  async getLearningRecommendations() {
    const response = await apiClient.get('/ai/learning-recommendations');
    return response.data;
  },

  async getAIUsageMetrics(timePeriod = 'week') {
    const params = { time_period: timePeriod };
    const response = await apiClient.get('/ai/usage-metrics', { params });
    return response.data;
  },

  async getAIPerformanceMetrics(timePeriod = 'week') {
    const params = { time_period: timePeriod };
    const response = await apiClient.get('/ai/performance-metrics', { params });
    return response.data;
  },

  async processMaterialForAI(materialId: string) {
    const response = await apiClient.post(`/ai/process-material/${materialId}`);
    return response.data;
  },

  async generateCourseQuiz(courseId: string, numQuestions = 10, difficulty = 'medium') {
    const params = { num_questions: numQuestions, difficulty };
    const response = await apiClient.post(`/ai/generate-course-quiz/${courseId}`, null, { params });
    return response.data;
  },

  async askAI(data: AIInteractionCreate) {
    const response = await apiClient.post('/ai/ask', data);
    return response.data;
  },

  async semanticSearch(data: AISearchQuery) {
    const response = await apiClient.post('/ai/search', data);
    return response.data;
  },

  async generateQuiz(data: AIQuizGenerationRequest) {
    const response = await apiClient.post('/ai/generate-quiz', data);
    return response.data;
  },

  async explainContent(data: AIExplanationRequest) {
    const response = await apiClient.post('/ai/explain', data);
    return response.data;
  },
};

export default aiService;
