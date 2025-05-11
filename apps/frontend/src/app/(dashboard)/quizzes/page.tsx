'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { quizService } from '@/lib/api';
import { formatDate } from '@/lib/utils';

type Quiz = {
  id: string;
  title: string;
  description: string;
  course_id: string;
  course_title: string;
  question_count: number;
  time_limit_minutes: number;
  created_at: string;
  status: 'completed' | 'in_progress' | 'not_started';
  score?: number;
};

export default function QuizzesPage() {
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'all' | 'completed' | 'pending'>('all');

  useEffect(() => {
    const fetchQuizzes = async () => {
      try {
        setIsLoading(true);
        // In a real implementation, this would call the actual API
        // const response = await quizService.getUserQuizzes();
        
        // Mock data for now
        setTimeout(() => {
          const mockQuizzes: Quiz[] = [
            {
              id: '1',
              title: 'Machine Learning Fundamentals',
              description: 'Test your knowledge of basic machine learning concepts',
              course_id: '1',
              course_title: 'Introduction to Machine Learning',
              question_count: 10,
              time_limit_minutes: 15,
              created_at: '2025-05-05T14:30:00Z',
              status: 'completed',
              score: 85,
            },
            {
              id: '2',
              title: 'SQL Advanced Queries',
              description: 'Test your knowledge of complex SQL queries and optimization',
              course_id: '2',
              course_title: 'Advanced Database Systems',
              question_count: 15,
              time_limit_minutes: 25,
              created_at: '2025-05-07T10:15:00Z',
              status: 'in_progress',
            },
            {
              id: '3',
              title: 'React Component Lifecycle',
              description: 'Test your understanding of React component lifecycle methods',
              course_id: '3',
              course_title: 'Web Development with React',
              question_count: 12,
              time_limit_minutes: 20,
              created_at: '2025-05-08T09:45:00Z',
              status: 'not_started',
            },
            {
              id: '4',
              title: 'Neural Networks Quiz',
              description: 'Test your knowledge of neural network architectures and training',
              course_id: '1',
              course_title: 'Introduction to Machine Learning',
              question_count: 8,
              time_limit_minutes: 12,
              created_at: '2025-05-06T16:20:00Z',
              status: 'completed',
              score: 92,
            },
          ];
          
          setQuizzes(mockQuizzes);
          setIsLoading(false);
        }, 1000);
      } catch (error) {
        console.error('Error fetching quizzes:', error);
        setIsLoading(false);
      }
    };

    fetchQuizzes();
  }, []);

  const filteredQuizzes = quizzes.filter(quiz => {
    if (activeTab === 'all') return true;
    if (activeTab === 'completed') return quiz.status === 'completed';
    if (activeTab === 'pending') return quiz.status === 'not_started' || quiz.status === 'in_progress';
    return true;
  });

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

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Quizzes</h1>
      </div>

      <div className="flex space-x-2 border-b pb-2">
        <Button
          variant={activeTab === 'all' ? 'primary' : 'ghost'}
          onClick={() => setActiveTab('all')}
        >
          All Quizzes
        </Button>
        <Button
          variant={activeTab === 'pending' ? 'primary' : 'ghost'}
          onClick={() => setActiveTab('pending')}
        >
          Pending
        </Button>
        <Button
          variant={activeTab === 'completed' ? 'primary' : 'ghost'}
          onClick={() => setActiveTab('completed')}
        >
          Completed
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
        </div>
      ) : filteredQuizzes.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredQuizzes.map((quiz) => (
            <Card key={quiz.id} className="flex flex-col">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <CardTitle>{quiz.title}</CardTitle>
                  {getStatusBadge(quiz.status)}
                </div>
                <CardDescription>{quiz.description}</CardDescription>
              </CardHeader>
              <CardContent className="flex-grow">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Course:</span>
                    <span className="font-medium">{quiz.course_title}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Questions:</span>
                    <span className="font-medium">{quiz.question_count}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Time Limit:</span>
                    <span className="font-medium">{quiz.time_limit_minutes} minutes</span>
                  </div>
                  {quiz.status === 'completed' && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Score:</span>
                      <span className="font-medium">{quiz.score}%</span>
                    </div>
                  )}
                </div>
              </CardContent>
              <CardFooter className="border-t pt-4">
                {quiz.status === 'completed' ? (
                  <div className="w-full grid grid-cols-2 gap-2">
                    <Link href={`/quizzes/${quiz.id}/review`} className="w-full">
                      <Button variant="outline" className="w-full">
                        Review
                      </Button>
                    </Link>
                    <Link href={`/quizzes/${quiz.id}/retake`} className="w-full">
                      <Button variant="outline" className="w-full">
                        Retake
                      </Button>
                    </Link>
                  </div>
                ) : quiz.status === 'in_progress' ? (
                  <Link href={`/quizzes/${quiz.id}/continue`} className="w-full">
                    <Button className="w-full">
                      Continue Quiz
                    </Button>
                  </Link>
                ) : (
                  <Link href={`/quizzes/${quiz.id}/start`} className="w-full">
                    <Button className="w-full">
                      Start Quiz
                    </Button>
                  </Link>
                )}
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900">No quizzes found</h3>
          <p className="mt-2 text-gray-500">
            {activeTab === 'all' 
              ? 'There are no quizzes available for your courses.'
              : activeTab === 'completed'
                ? 'You haven\'t completed any quizzes yet.'
                : 'You don\'t have any pending quizzes.'}
          </p>
        </div>
      )}
    </div>
  );
}
