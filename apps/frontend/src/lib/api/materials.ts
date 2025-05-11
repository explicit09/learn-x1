import apiClient from './client';

export interface Material {
  id: string;
  title: string;
  description: string;
  course_id: string;
  order: number;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface MaterialCreate {
  title: string;
  description: string;
  course_id: string;
  order?: number;
  is_published?: boolean;
}

export interface MaterialUpdate {
  title?: string;
  description?: string;
  order?: number;
  is_published?: boolean;
}

export interface Content {
  id: string;
  material_id: string;
  title: string;
  content_type: string;
  content_text: string;
  order: number;
  created_at: string;
  updated_at: string;
}

export interface ContentCreate {
  material_id: string;
  title: string;
  content_type: string;
  content_text: string;
  order?: number;
}

export interface ContentUpdate {
  title?: string;
  content_type?: string;
  content_text?: string;
  order?: number;
}

const materialService = {
  async getMaterialsForCourse(courseId: string, page = 1, perPage = 10, publishedOnly = false) {
    const params = { page, per_page: perPage, published_only: publishedOnly };
    const response = await apiClient.get(`/materials/course/${courseId}`, { params });
    return response.data;
  },

  async getMaterial(id: string) {
    const response = await apiClient.get(`/materials/${id}`);
    return response.data;
  },

  async createMaterial(data: MaterialCreate) {
    const response = await apiClient.post('/materials', data);
    return response.data;
  },

  async updateMaterial(id: string, data: MaterialUpdate) {
    const response = await apiClient.put(`/materials/${id}`, data);
    return response.data;
  },

  async deleteMaterial(id: string) {
    const response = await apiClient.delete(`/materials/${id}`);
    return response.data;
  },

  // Content endpoints
  async getContentsForMaterial(materialId: string, page = 1, perPage = 10) {
    const params = { page, per_page: perPage };
    const response = await apiClient.get(`/materials/${materialId}/contents`, { params });
    return response.data;
  },

  async getContent(id: string) {
    const response = await apiClient.get(`/materials/content/${id}`);
    return response.data;
  },

  async createContent(data: ContentCreate) {
    const response = await apiClient.post('/materials/content', data);
    return response.data;
  },

  async updateContent(id: string, data: ContentUpdate) {
    const response = await apiClient.put(`/materials/content/${id}`, data);
    return response.data;
  },

  async deleteContent(id: string) {
    const response = await apiClient.delete(`/materials/content/${id}`);
    return response.data;
  },
};

export default materialService;
