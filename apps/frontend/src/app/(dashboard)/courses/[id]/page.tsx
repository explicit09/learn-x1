'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { courseService, materialService, quizService } from '@/lib/api';
import { formatDate } from '@/lib/utils';

type Material = {
  id: string;
  title: string;
  type: string;
  order: number;
  status: string;
  created_at: string;
};

type Quiz = {
  id: string;
  title: string;
  description: string;
  question_count: number;
  time_limit_minutes: number;
  status: string;
};

export default function CourseDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [course, setCourse] = useState<any>(null);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'materials' | 'quizzes'>('materials');

  useEffect(() => {
    const fetchCourseData = async () => {
      try {
        setIsLoading(true);
        // In a real implementation, these would call the actual API
        // const courseResponse = await courseService.getCourse(params.id);
        // const materialsResponse = await materialService.getMaterialsForCourse(params.id);
        // const quizzesResponse = await quizService.getQuizzesForCourse(params.id);
        
        // Mock data for now
        setTimeout(() => {
          // Mock course data
          setCourse({
            id: params.id,
            title: params.id === '1' ? 'Introduction to Machine Learning' : 
                   params.id === '2' ? 'Advanced Database Systems' : 'Web Development with React',
            description: 'This course provides a comprehensive introduction to the field of machine learning, covering fundamental concepts, algorithms, and practical applications.',
            instructor: 'Dr. Jane Smith',
            status: 'published',
            created_at: '2025-04-15T10:00:00Z',
            updated_at: '2025-05-01T14:30:00Z',
            enrollment_count: 156,
            average_rating: 4.8,
            duration_hours: 24,
            level: 'Intermediate',
            prerequisites: ['Basic programming knowledge', 'Fundamentals of statistics'],
            learning_objectives: [
              'Understand core machine learning concepts',
              'Implement common algorithms from scratch',
              'Apply machine learning to real-world problems',
              'Evaluate and improve model performance'
            ]
          });
          
          // Mock materials data
          setMaterials([
            {
              id: '101',
              title: 'Introduction to the Course',
              type: 'video',
              order: 1,
              status: 'completed',
              created_at: '2025-04-15T10:00:00Z',
            },
            {
              id: '102',
              title: 'Supervised Learning Fundamentals',
              type: 'document',
              order: 2,
              status: 'completed',
              created_at: '2025-04-16T10:00:00Z',
            },
            {
              id: '103',
              title: 'Linear Regression Implementation',
              type: 'interactive',
              order: 3,
              status: 'in_progress',
              created_at: '2025-04-17T10:00:00Z',
            },
            {
              id: '104',
              title: 'Classification Algorithms',
              type: 'video',
              order: 4,
              status: 'not_started',
              created_at: '2025-04-18T10:00:00Z',
            },
            {
              id: '105',
              title: 'Neural Networks Introduction',
              type: 'document',
              order: 5,
              status: 'not_started',
              created_at: '2025-04-19T10:00:00Z',
            },
          ]);
          
          // Mock quizzes data
          setQuizzes([
            {
              id: '201',
              title: 'Machine Learning Fundamentals Quiz',
              description: 'Test your understanding of basic machine learning concepts',
              question_count: 10,
              time_limit_minutes: 15,
              status: 'completed',
            },
            {
              id: '202',
              title: 'Linear Regression Quiz',
              description: 'Test your knowledge of linear regression implementation and theory',
              question_count: 8,
              time_limit_minutes: 12,
              status: 'not_started',
            },
            {
              id: '203',
              title: 'Classification Algorithms Quiz',
              description: 'Test your understanding of various classification methods',
              question_count: 12,
              time_limit_minutes: 20,
              status: 'not_started',
            },
          ]);
          
          setIsLoading(false);
        }, 1000);
      } catch (error) {
        console.error('Error fetching course data:', error);
        setIsLoading(false);
      }
    };

    fetchCourseData();
  }, [params.id]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">Completed</span>;
      case 'in_progress':
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">In Progress</span>;
      case 'not_started':
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">Not Started</span>;
      default:
        return null;
    }
  };

  const getMaterialIcon = (type: string) => {
    switch (type) {
      case 'video':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-600" viewBox="0 0 20 20" fill="currentColor">
            <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
          </svg>
        );
      case 'document':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-600" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
          </svg>
        );
      case 'interactive':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-600" viewBox="0 0 20 20" fill="currentColor">
            <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
          </svg>
        );
      default:
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-600" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900">Course not found</h3>
        <p className="mt-2 text-gray-500">
          The course you are looking for does not exist or has been removed.
        </p>
        <Link href="/courses">
          <Button className="mt-4">Browse Courses</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Link href="/courses">
          <Button variant="ghost" size="sm" className="flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
            </svg>
            Back to Courses
          </Button>
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="bg-gradient-to-r from-primary-600 to-primary-800 p-6 text-white">
          <h1 className="text-3xl font-bold">{course.title}</h1>
          <div className="mt-2 flex items-center gap-2">
            <span className="text-sm opacity-90">Instructor: {course.instructor}</span>
            <span className="text-sm opacity-90">•</span>
            <span className="text-sm opacity-90">Level: {course.level}</span>
            <span className="text-sm opacity-90">•</span>
            <span className="text-sm opacity-90">{course.duration_hours} hours</span>
          </div>
        </div>
        
        <div className="p-6">
          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">About this course</h2>
            <p className="text-gray-700">{course.description}</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <h3 className="text-lg font-medium mb-2">Prerequisites</h3>
              <ul className="list-disc pl-5 space-y-1 text-gray-700">
                {course.prerequisites.map((prerequisite: string, index: number) => (
                  <li key={index}>{prerequisite}</li>
                ))}
              </ul>
            </div>
            
            <div>
              <h3 className="text-lg font-medium mb-2">Learning Objectives</h3>
              <ul className="list-disc pl-5 space-y-1 text-gray-700">
                {course.learning_objectives.map((objective: string, index: number) => (
                  <li key={index}>{objective}</li>
                ))}
              </ul>
            </div>
          </div>
          
          <div className="flex justify-between items-center mb-4">
            <div className="flex space-x-4">
              <Button 
                variant={activeTab === 'materials' ? 'primary' : 'outline'}
                onClick={() => setActiveTab('materials')}
              >
                Course Materials
              </Button>
              <Button 
                variant={activeTab === 'quizzes' ? 'primary' : 'outline'}
                onClick={() => setActiveTab('quizzes')}
              >
                Quizzes
              </Button>
            </div>
            
            <Button>
              Continue Learning
            </Button>
          </div>
          
          {activeTab === 'materials' ? (
            <div className="space-y-4">
              {materials.map((material) => (
                <div key={material.id} className="border rounded-lg p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="bg-gray-100 p-2 rounded-full">
                      {getMaterialIcon(material.type)}
                    </div>
                    <div>
                      <h4 className="font-medium">{material.title}</h4>
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <span className="capitalize">{material.type}</span>
                        <span>•</span>
                        <span>Order: {material.order}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {getStatusBadge(material.status)}
                    <Link href={`/courses/${params.id}/materials/${material.id}`}>
                      <Button variant="outline" size="sm">
                        {material.status === 'completed' ? 'Review' : material.status === 'in_progress' ? 'Continue' : 'Start'}
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {quizzes.map((quiz) => (
                <div key={quiz.id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium">{quiz.title}</h4>
                    {getStatusBadge(quiz.status)}
                  </div>
                  <p className="text-gray-600 text-sm mb-4">{quiz.description}</p>
                  <div className="flex justify-between items-center">
                    <div className="text-sm text-gray-500">
                      <span>{quiz.question_count} questions</span>
                      <span className="mx-2">•</span>
                      <span>{quiz.time_limit_minutes} minutes</span>
                    </div>
                    <Link href={`/courses/${params.id}/quizzes/${quiz.id}`}>
                      <Button variant="outline" size="sm">
                        {quiz.status === 'completed' ? 'Review' : 'Start Quiz'}
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
