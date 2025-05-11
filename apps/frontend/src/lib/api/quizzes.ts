import apiClient from './client';

export interface Quiz {
  id: string;
  title: string;
  description: string;
  course_id: string;
  is_published: boolean;
  time_limit_minutes: number | null;
  passing_score: number;
  created_at: string;
  updated_at: string;
}

export interface QuizCreate {
  title: string;
  description: string;
  course_id: string;
  is_published?: boolean;
  time_limit_minutes?: number | null;
  passing_score?: number;
}

export interface QuizUpdate {
  title?: string;
  description?: string;
  is_published?: boolean;
  time_limit_minutes?: number | null;
  passing_score?: number;
}

export interface Question {
  id: string;
  quiz_id: string;
  question_text: string;
  question_type: string; // 'multiple_choice', 'true_false', 'short_answer'
  options?: Array<{
    id: string;
    text: string;
    is_correct: boolean;
  }>;
  correct_answer?: string;
  explanation?: string;
  points: number;
  difficulty: string; // 'easy', 'medium', 'hard'
  created_at: string;
  updated_at: string;
}

export interface QuestionCreate {
  quiz_id: string;
  question_text: string;
  question_type: string;
  options?: Array<{
    text: string;
    is_correct: boolean;
  }>;
  correct_answer?: string;
  explanation?: string;
  points?: number;
  difficulty?: string;
}

export interface QuestionUpdate {
  question_text?: string;
  question_type?: string;
  options?: Array<{
    id?: string;
    text: string;
    is_correct: boolean;
  }>;
  correct_answer?: string;
  explanation?: string;
  points?: number;
  difficulty?: string;
}

export interface SubmissionCreate {
  quiz_id: string;
  answers: Array<{
    question_id: string;
    answer: string; // Option ID for multiple choice, 'true'/'false' for true/false, text for short answer
  }>;
}

export interface Submission {
  id: string;
  user_id: string;
  quiz_id: string;
  score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  completed_at: string;
  created_at: string;
}

export interface SubmissionWithDetails extends Submission {
  answers: Array<{
    question_id: string;
    question_text: string;
    question_type: string;
    user_answer: string;
    correct_answer: string;
    is_correct: boolean;
    points_earned: number;
    max_points: number;
    explanation?: string;
  }>;
}

const quizService = {
  async getQuizzesForCourse(courseId: string, page = 1, perPage = 10, publishedOnly = false) {
    const params = { page, per_page: perPage, published_only: publishedOnly };
    const response = await apiClient.get(`/quizzes/course/${courseId}`, { params });
    return response.data;
  },

  async getQuiz(id: string) {
    const response = await apiClient.get(`/quizzes/${id}`);
    return response.data;
  },

  async createQuiz(data: QuizCreate) {
    const response = await apiClient.post('/quizzes', data);
    return response.data;
  },

  async updateQuiz(id: string, data: QuizUpdate) {
    const response = await apiClient.put(`/quizzes/${id}`, data);
    return response.data;
  },

  async deleteQuiz(id: string) {
    const response = await apiClient.delete(`/quizzes/${id}`);
    return response.data;
  },

  // Question endpoints
  async getQuestionsForQuiz(quizId: string, page = 1, perPage = 10) {
    const params = { page, per_page: perPage };
    const response = await apiClient.get(`/quizzes/${quizId}/questions`, { params });
    return response.data;
  },

  async createQuestion(data: QuestionCreate) {
    const response = await apiClient.post('/quizzes/questions', data);
    return response.data;
  },

  async updateQuestion(id: string, data: QuestionUpdate) {
    const response = await apiClient.put(`/quizzes/questions/${id}`, data);
    return response.data;
  },

  async deleteQuestion(id: string) {
    const response = await apiClient.delete(`/quizzes/questions/${id}`);
    return response.data;
  },

  // Submission endpoints
  async submitQuiz(data: SubmissionCreate) {
    const response = await apiClient.post('/quizzes/submissions', data);
    return response.data;
  },

  async getUserSubmissions(page = 1, perPage = 10) {
    const params = { page, per_page: perPage };
    const response = await apiClient.get('/quizzes/submissions', { params });
    return response.data;
  },

  async getSubmission(id: string) {
    const response = await apiClient.get(`/quizzes/submissions/${id}`);
    return response.data;
  },
};

export default quizService;
