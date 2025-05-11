'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

type ContentItem = {
  id: string;
  title: string;
  type: 'video' | 'document' | 'interactive' | 'quiz';
  course_title: string;
  course_id: string;
  status: 'draft' | 'published' | 'archived';
  created_at: string;
  updated_at: string;
};

export default function ProfessorContentPage() {
  const [contentItems, setContentItems] = useState<ContentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    const fetchContent = async () => {
      try {
        setIsLoading(true);
        
        // Mock data for now
        setTimeout(() => {
          const mockContent: ContentItem[] = [
            {
              id: '101',
              title: 'Introduction to Machine Learning',
              type: 'video',
              course_title: 'Introduction to Machine Learning',
              course_id: '1',
              status: 'published',
              created_at: '2025-04-15T10:00:00Z',
              updated_at: '2025-04-15T10:00:00Z',
            },
            {
              id: '102',
              title: 'Supervised Learning Fundamentals',
              type: 'document',
              course_title: 'Introduction to Machine Learning',
              course_id: '1',
              status: 'published',
              created_at: '2025-04-16T10:00:00Z',
              updated_at: '2025-04-16T10:00:00Z',
            },
            {
              id: '103',
              title: 'Linear Regression Implementation',
              type: 'interactive',
              course_title: 'Introduction to Machine Learning',
              course_id: '1',
              status: 'published',
              created_at: '2025-04-17T10:00:00Z',
              updated_at: '2025-04-17T10:00:00Z',
            },
            {
              id: '104',
              title: 'Classification Algorithms',
              type: 'video',
              course_title: 'Introduction to Machine Learning',
              course_id: '1',
              status: 'draft',
              created_at: '2025-04-18T10:00:00Z',
              updated_at: '2025-04-18T10:00:00Z',
            },
            {
              id: '201',
              title: 'Database Normalization',
              type: 'document',
              course_title: 'Advanced Database Systems',
              course_id: '2',
              status: 'published',
              created_at: '2025-04-10T09:15:00Z',
              updated_at: '2025-04-10T09:15:00Z',
            },
            {
              id: '202',
              title: 'SQL Query Optimization',
              type: 'interactive',
              course_title: 'Advanced Database Systems',
              course_id: '2',
              status: 'published',
              created_at: '2025-04-11T14:30:00Z',
              updated_at: '2025-04-11T14:30:00Z',
            },
            {
              id: '301',
              title: 'React Component Lifecycle',
              type: 'video',
              course_title: 'Web Development with React',
              course_id: '3',
              status: 'published',
              created_at: '2025-03-22T14:20:00Z',
              updated_at: '2025-03-22T14:20:00Z',
            },
            {
              id: '302',
              title: 'State Management in React',
              type: 'document',
              course_title: 'Web Development with React',
              course_id: '3',
              status: 'published',
              created_at: '2025-03-23T11:45:00Z',
              updated_at: '2025-03-23T11:45:00Z',
            },
            {
              id: '303',
              title: 'Building a Todo App',
              type: 'interactive',
              course_title: 'Web Development with React',
              course_id: '3',
              status: 'draft',
              created_at: '2025-03-24T16:10:00Z',
              updated_at: '2025-03-24T16:10:00Z',
            },
            {
              id: '401',
              title: 'Data Visualization Principles',
              type: 'document',
              course_title: 'Data Visualization Techniques',
              course_id: '4',
              status: 'draft',
              created_at: '2025-05-05T08:45:00Z',
              updated_at: '2025-05-05T08:45:00Z',
            },
          ];
          
          setContentItems(mockContent);
          setIsLoading(false);
        }, 1000);
      } catch (error) {
        console.error('Error fetching content:', error);
        setIsLoading(false);
      }
    };

    fetchContent();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real implementation, this would trigger an API call with the search query
  };

  const filteredContent = contentItems.filter(item => {
    // Filter by search query
    const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                         item.course_title.toLowerCase().includes(searchQuery.toLowerCase());
    
    // Filter by type
    const matchesType = typeFilter === 'all' || item.type === typeFilter;
    
    // Filter by status
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
    
    return matchesSearch && matchesType && matchesStatus;
  });

  const getContentTypeIcon = (type: string) => {
    switch (type) {
      case 'video':
        return (
          <div className="p-2 bg-blue-100 rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-600" viewBox="0 0 20 20" fill="currentColor">
              <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
            </svg>
          </div>
        );
      case 'document':
        return (
          <div className="p-2 bg-green-100 rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-600" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
            </svg>
          </div>
        );
      case 'interactive':
        return (
          <div className="p-2 bg-purple-100 rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-purple-600" viewBox="0 0 20 20" fill="currentColor">
              <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
            </svg>
          </div>
        );
      case 'quiz':
        return (
          <div className="p-2 bg-yellow-100 rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-yellow-600" viewBox="0 0 20 20" fill="currentColor">
              <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
              <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
            </svg>
          </div>
        );
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'published':
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">Published</span>;
      case 'draft':
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">Draft</span>;
      case 'archived':
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">Archived</span>;
      default:
        return null;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Course Content</h1>
        <div className="flex space-x-2">
          <Link href="/professor/content/create">
            <Button>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
              </svg>
              Create Content
            </Button>
          </Link>
        </div>
      </div>

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <form onSubmit={handleSearch} className="w-full md:w-auto">
          <div className="flex gap-2">
            <Input
              type="text"
              placeholder="Search content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full md:w-64"
            />
            <Button type="submit">Search</Button>
          </div>
        </form>

        <div className="flex flex-wrap gap-2">
          <div className="flex space-x-2">
            <Button 
              variant={typeFilter === 'all' ? 'primary' : 'outline'}
              onClick={() => setTypeFilter('all')}
              size="sm"
            >
              All Types
            </Button>
            <Button 
              variant={typeFilter === 'video' ? 'primary' : 'outline'}
              onClick={() => setTypeFilter('video')}
              size="sm"
            >
              Videos
            </Button>
            <Button 
              variant={typeFilter === 'document' ? 'primary' : 'outline'}
              onClick={() => setTypeFilter('document')}
              size="sm"
            >
              Documents
            </Button>
            <Button 
              variant={typeFilter === 'interactive' ? 'primary' : 'outline'}
              onClick={() => setTypeFilter('interactive')}
              size="sm"
            >
              Interactive
            </Button>
          </div>
          
          <div className="flex space-x-2 mt-2 md:mt-0">
            <Button 
              variant={statusFilter === 'all' ? 'primary' : 'outline'}
              onClick={() => setStatusFilter('all')}
              size="sm"
            >
              All Status
            </Button>
            <Button 
              variant={statusFilter === 'published' ? 'primary' : 'outline'}
              onClick={() => setStatusFilter('published')}
              size="sm"
            >
              Published
            </Button>
            <Button 
              variant={statusFilter === 'draft' ? 'primary' : 'outline'}
              onClick={() => setStatusFilter('draft')}
              size="sm"
            >
              Draft
            </Button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
        </div>
      ) : filteredContent.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Content List</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="py-3 px-4 text-left font-medium text-gray-500">Content</th>
                    <th className="py-3 px-4 text-left font-medium text-gray-500">Type</th>
                    <th className="py-3 px-4 text-left font-medium text-gray-500">Course</th>
                    <th className="py-3 px-4 text-left font-medium text-gray-500">Status</th>
                    <th className="py-3 px-4 text-left font-medium text-gray-500">Created</th>
                    <th className="py-3 px-4 text-right font-medium text-gray-500">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredContent.map((item) => (
                    <tr key={item.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4">
                        <div className="font-medium">{item.title}</div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          {getContentTypeIcon(item.type)}
                          <span className="capitalize">{item.type}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <Link href={`/professor/courses/${item.course_id}`} className="text-primary-600 hover:underline">
                          {item.course_title}
                        </Link>
                      </td>
                      <td className="py-3 px-4">
                        {getStatusBadge(item.status)}
                      </td>
                      <td className="py-3 px-4">{formatDate(item.created_at)}</td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex justify-end gap-2">
                          <Link href={`/professor/content/${item.id}/edit`}>
                            <Button variant="outline" size="sm">
                              Edit
                            </Button>
                          </Link>
                          <Link href={`/professor/content/${item.id}/preview`}>
                            <Button variant="outline" size="sm">
                              Preview
                            </Button>
                          </Link>
                          {item.status === 'draft' && (
                            <Button variant="primary" size="sm">
                              Publish
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900">No content found</h3>
          <p className="mt-2 text-gray-500">
            {searchQuery || typeFilter !== 'all' || statusFilter !== 'all'
              ? 'No content matches your search criteria.'
              : 'You haven\'t created any content yet.'}
          </p>
          <Link href="/professor/content/create">
            <Button className="mt-4">
              Create Your First Content
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
