import apiClient from './client';

export interface Course {
  id: string;
  title: string;
  description: string;
  status: string;
  organization_id: string;
  created_at: string;
  updated_at: string;
}

export interface CourseCreate {
  title: string;
  description: string;
  status: string;
}

export interface CourseUpdate {
  title?: string;
  description?: string;
  status?: string;
}

const courseService = {
  async getCourses(page = 1, perPage = 10, status?: string, search?: string) {
    const params = { page, per_page: perPage };
    if (status) Object.assign(params, { status });
    if (search) Object.assign(params, { search });
    
    const response = await apiClient.get('/courses', { params });
    return response.data;
  },

  async getCourse(id: string) {
    const response = await apiClient.get(`/courses/${id}`);
    return response.data;
  },

  async createCourse(data: CourseCreate) {
    const response = await apiClient.post('/courses', data);
    return response.data;
  },

  async updateCourse(id: string, data: CourseUpdate) {
    const response = await apiClient.put(`/courses/${id}`, data);
    return response.data;
  },

  async deleteCourse(id: string) {
    const response = await apiClient.delete(`/courses/${id}`);
    return response.data;
  },

  async getCourseStats(id: string) {
    const response = await apiClient.get(`/courses/${id}/stats`);
    return response.data;
  },

  async enrollInCourse(id: string) {
    const response = await apiClient.post(`/courses/${id}/enroll`);
    return response.data;
  },

  async unenrollFromCourse(id: string) {
    const response = await apiClient.delete(`/courses/${id}/enroll`);
    return response.data;
  },
};

export default courseService;
