'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { courseService, materialService } from '@/lib/api';
import { formatDate } from '@/lib/utils';

type CourseProgress = {
  id: string;
  title: string;
  description: string;
  progress: number;
  last_accessed: string;
  total_materials: number;
  completed_materials: number;
};

export default function MyLearningPage() {
  const [courses, setCourses] = useState<CourseProgress[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchUserCourses = async () => {
      try {
        setIsLoading(true);
        // In a real implementation, this would call the actual API
        // const response = await courseService.getUserCourses();
        
        // Mock data for now
        setTimeout(() => {
          setCourses([
            {
              id: '1',
              title: 'Introduction to Machine Learning',
              description: 'Learn the fundamentals of machine learning algorithms and applications',
              progress: 65,
              last_accessed: '2025-05-07T14:30:00Z',
              total_materials: 12,
              completed_materials: 8,
            },
            {
              id: '2',
              title: 'Advanced Database Systems',
              description: 'Deep dive into database architecture, optimization, and advanced queries',
              progress: 30,
              last_accessed: '2025-05-08T10:15:00Z',
              total_materials: 15,
              completed_materials: 4,
            },
            {
              id: '3',
              title: 'Web Development with React',
              description: 'Build modern web applications with React and related technologies',
              progress: 90,
              last_accessed: '2025-05-09T09:45:00Z',
              total_materials: 10,
              completed_materials: 9,
            },
          ]);
          setIsLoading(false);
        }, 1000);
      } catch (error) {
        console.error('Error fetching user courses:', error);
        setIsLoading(false);
      }
    };

    fetchUserCourses();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">My Learning</h1>
        <Link href="/courses">
          <Button variant="outline">Browse Courses</Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
        </div>
      ) : courses.length > 0 ? (
        <div className="space-y-6">
          {courses.map((course) => (
            <Card key={course.id} className="overflow-hidden">
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-xl">{course.title}</CardTitle>
                  <div className="text-sm text-gray-500">
                    Last accessed: {formatDate(course.last_accessed, 'PP')}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">{course.description}</p>
                
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span>Progress: {course.progress}%</span>
                    <span>
                      {course.completed_materials}/{course.total_materials} materials completed
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-primary-600 h-2.5 rounded-full" 
                      style={{ width: `${course.progress}%` }}
                    ></div>
                  </div>
                </div>
                
                <div className="flex space-x-3">
                  <Link href={`/courses/${course.id}`} className="flex-1">
                    <Button variant="outline" className="w-full">View Course</Button>
                  </Link>
                  <Link href={`/courses/${course.id}/continue`} className="flex-1">
                    <Button className="w-full">Continue Learning</Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900">No courses enrolled</h3>
          <p className="mt-2 text-gray-500">
            You haven't enrolled in any courses yet. Browse our catalog to get started.
          </p>
          <Link href="/courses">
            <Button className="mt-4">Browse Courses</Button>
          </Link>
        </div>
      )}
    </div>
  );
}
