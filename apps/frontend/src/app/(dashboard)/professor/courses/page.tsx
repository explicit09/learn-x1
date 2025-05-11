'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { formatDate } from '@/lib/utils';

type Course = {
  id: string;
  title: string;
  description: string;
  status: 'draft' | 'published' | 'archived';
  created_at: string;
  updated_at: string;
  student_count: number;
  completion_rate: number;
};

export default function ProfessorCoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        setIsLoading(true);
        
        // Mock data for now
        setTimeout(() => {
          const mockCourses: Course[] = [
            {
              id: '1',
              title: 'Introduction to Machine Learning',
              description: 'A comprehensive introduction to machine learning concepts and algorithms.',
              status: 'published',
              created_at: '2025-04-15T10:00:00Z',
              updated_at: '2025-05-01T14:30:00Z',
              student_count: 78,
              completion_rate: 65
            },
            {
              id: '2',
              title: 'Advanced Database Systems',
              description: 'Deep dive into database architecture, optimization, and advanced queries.',
              status: 'published',
              created_at: '2025-04-10T09:15:00Z',
              updated_at: '2025-04-28T11:45:00Z',
              student_count: 42,
              completion_rate: 48
            },
            {
              id: '3',
              title: 'Web Development with React',
              description: 'Learn modern web development using React and related technologies.',
              status: 'published',
              created_at: '2025-03-22T14:20:00Z',
              updated_at: '2025-04-15T16:10:00Z',
              student_count: 65,
              completion_rate: 72
            },
            {
              id: '4',
              title: 'Data Visualization Techniques',
              description: 'Explore methods for effective data visualization and communication.',
              status: 'draft',
              created_at: '2025-05-05T08:45:00Z',
              updated_at: '2025-05-08T15:30:00Z',
              student_count: 0,
              completion_rate: 0
            },
            {
              id: '5',
              title: 'Natural Language Processing',
              description: 'Introduction to NLP concepts and applications in modern AI systems.',
              status: 'archived',
              created_at: '2024-11-10T11:30:00Z',
              updated_at: '2025-01-15T09:20:00Z',
              student_count: 32,
              completion_rate: 94
            },
          ];
          
          setCourses(mockCourses);
          setIsLoading(false);
        }, 1000);
      } catch (error) {
        console.error('Error fetching courses:', error);
        setIsLoading(false);
      }
    };

    fetchCourses();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real implementation, this would trigger an API call with the search query
  };

  const filteredCourses = courses.filter(course => {
    // Filter by search query
    const matchesSearch = course.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                         course.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    // Filter by status
    const matchesStatus = statusFilter === 'all' || course.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

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

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">My Courses</h1>
        <Link href="/professor/courses/create">
          <Button>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            Create Course
          </Button>
        </Link>
      </div>

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <form onSubmit={handleSearch} className="w-full md:w-auto">
          <div className="flex gap-2">
            <Input
              type="text"
              placeholder="Search courses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full md:w-64"
            />
            <Button type="submit">Search</Button>
          </div>
        </form>

        <div className="flex space-x-2">
          <Button 
            variant={statusFilter === 'all' ? 'primary' : 'outline'}
            onClick={() => setStatusFilter('all')}
            size="sm"
          >
            All
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
          <Button 
            variant={statusFilter === 'archived' ? 'primary' : 'outline'}
            onClick={() => setStatusFilter('archived')}
            size="sm"
          >
            Archived
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
        </div>
      ) : filteredCourses.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCourses.map((course) => (
            <Card key={course.id} className="flex flex-col">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <CardTitle className="text-xl">{course.title}</CardTitle>
                  {getStatusBadge(course.status)}
                </div>
                <CardDescription className="line-clamp-2">{course.description}</CardDescription>
              </CardHeader>
              <CardContent className="flex-grow">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Students:</span>
                    <span className="font-medium">{course.student_count}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Completion Rate:</span>
                    <span className="font-medium">{course.completion_rate}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Last Updated:</span>
                    <span className="font-medium">{formatDate(course.updated_at, 'PP')}</span>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="border-t pt-4 flex justify-between">
                <Link href={`/professor/courses/${course.id}`}>
                  <Button variant="outline">
                    View Details
                  </Button>
                </Link>
                <Link href={`/professor/courses/${course.id}/edit`}>
                  <Button variant="outline">
                    Edit
                  </Button>
                </Link>
                {course.status === 'draft' && (
                  <Button variant="primary">
                    Publish
                  </Button>
                )}
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900">No courses found</h3>
          <p className="mt-2 text-gray-500">
            {searchQuery
              ? `No courses matching "${searchQuery}"`
              : statusFilter !== 'all'
                ? `No ${statusFilter} courses found`
                : 'You haven\'t created any courses yet.'}
          </p>
          <Link href="/professor/courses/create">
            <Button className="mt-4">
              Create Your First Course
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
