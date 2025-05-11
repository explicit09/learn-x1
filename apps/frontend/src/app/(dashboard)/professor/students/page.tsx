'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

type Student = {
  id: string;
  name: string;
  email: string;
  enrolled_courses: number;
  completed_courses: number;
  last_active: string;
  average_score: number;
};

export default function ProfessorStudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<string>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    const fetchStudents = async () => {
      try {
        setIsLoading(true);
        
        // Mock data for now
        setTimeout(() => {
          const mockStudents: Student[] = [
            {
              id: '1',
              name: 'Alex Johnson',
              email: 'alex.johnson@example.com',
              enrolled_courses: 3,
              completed_courses: 1,
              last_active: '2025-05-09T10:30:00Z',
              average_score: 87
            },
            {
              id: '2',
              name: 'Maria Garcia',
              email: 'maria.garcia@example.com',
              enrolled_courses: 2,
              completed_courses: 0,
              last_active: '2025-05-09T09:45:00Z',
              average_score: 92
            },
            {
              id: '3',
              name: 'James Wilson',
              email: 'james.wilson@example.com',
              enrolled_courses: 1,
              completed_courses: 0,
              last_active: '2025-05-09T08:15:00Z',
              average_score: 0
            },
            {
              id: '4',
              name: 'Sarah Ahmed',
              email: 'sarah.ahmed@example.com',
              enrolled_courses: 4,
              completed_courses: 2,
              last_active: '2025-05-08T16:20:00Z',
              average_score: 95
            },
            {
              id: '5',
              name: 'David Chen',
              email: 'david.chen@example.com',
              enrolled_courses: 2,
              completed_courses: 1,
              last_active: '2025-05-07T14:10:00Z',
              average_score: 78
            },
            {
              id: '6',
              name: 'Emily Rodriguez',
              email: 'emily.rodriguez@example.com',
              enrolled_courses: 3,
              completed_courses: 3,
              last_active: '2025-05-06T11:30:00Z',
              average_score: 91
            },
          ];
          
          setStudents(mockStudents);
          setIsLoading(false);
        }, 1000);
      } catch (error) {
        console.error('Error fetching students:', error);
        setIsLoading(false);
      }
    };

    fetchStudents();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real implementation, this would trigger an API call with the search query
  };

  const handleSort = (field: string) => {
    if (sortBy === field) {
      // Toggle sort order if clicking the same field
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // Set new sort field and default to ascending
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const filteredStudents = students
    .filter(student => {
      return student.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
             student.email.toLowerCase().includes(searchQuery.toLowerCase());
    })
    .sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'enrolled':
          comparison = a.enrolled_courses - b.enrolled_courses;
          break;
        case 'completed':
          comparison = a.completed_courses - b.completed_courses;
          break;
        case 'score':
          comparison = a.average_score - b.average_score;
          break;
        case 'active':
          comparison = new Date(a.last_active).getTime() - new Date(b.last_active).getTime();
          break;
        default:
          comparison = 0;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getSortIcon = (field: string) => {
    if (sortBy !== field) return null;
    
    return sortOrder === 'asc' ? (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
      </svg>
    ) : (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
      </svg>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Students</h1>
        <Link href="/professor/students/invite">
          <Button>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016 6H2a6 6 0 016-6zM16 7a1 1 0 10-2 0v1h-1a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V7z" />
            </svg>
            Invite Students
          </Button>
        </Link>
      </div>

      <form onSubmit={handleSearch} className="w-full">
        <div className="flex gap-2">
          <Input
            type="text"
            placeholder="Search students by name or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full md:w-96"
          />
          <Button type="submit">Search</Button>
        </div>
      </form>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
        </div>
      ) : filteredStudents.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Student List</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th 
                      className="py-3 px-4 text-left font-medium text-gray-500 cursor-pointer"
                      onClick={() => handleSort('name')}
                    >
                      <div className="flex items-center">
                        Student Name
                        {getSortIcon('name')}
                      </div>
                    </th>
                    <th 
                      className="py-3 px-4 text-left font-medium text-gray-500 cursor-pointer"
                      onClick={() => handleSort('enrolled')}
                    >
                      <div className="flex items-center">
                        Enrolled Courses
                        {getSortIcon('enrolled')}
                      </div>
                    </th>
                    <th 
                      className="py-3 px-4 text-left font-medium text-gray-500 cursor-pointer"
                      onClick={() => handleSort('completed')}
                    >
                      <div className="flex items-center">
                        Completed
                        {getSortIcon('completed')}
                      </div>
                    </th>
                    <th 
                      className="py-3 px-4 text-left font-medium text-gray-500 cursor-pointer"
                      onClick={() => handleSort('score')}
                    >
                      <div className="flex items-center">
                        Avg. Score
                        {getSortIcon('score')}
                      </div>
                    </th>
                    <th 
                      className="py-3 px-4 text-left font-medium text-gray-500 cursor-pointer"
                      onClick={() => handleSort('active')}
                    >
                      <div className="flex items-center">
                        Last Active
                        {getSortIcon('active')}
                      </div>
                    </th>
                    <th className="py-3 px-4 text-right font-medium text-gray-500">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStudents.map((student) => (
                    <tr key={student.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4">
                        <div>
                          <div className="font-medium">{student.name}</div>
                          <div className="text-sm text-gray-500">{student.email}</div>
                        </div>
                      </td>
                      <td className="py-3 px-4">{student.enrolled_courses}</td>
                      <td className="py-3 px-4">{student.completed_courses}</td>
                      <td className="py-3 px-4">
                        {student.average_score > 0 ? (
                          <span className={`font-medium ${student.average_score >= 90 ? 'text-green-600' : student.average_score >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>
                            {student.average_score}%
                          </span>
                        ) : (
                          <span className="text-gray-500">N/A</span>
                        )}
                      </td>
                      <td className="py-3 px-4">{formatDate(student.last_active)}</td>
                      <td className="py-3 px-4 text-right">
                        <Link href={`/professor/students/${student.id}`}>
                          <Button variant="outline" size="sm">
                            View Profile
                          </Button>
                        </Link>
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
          <h3 className="text-lg font-medium text-gray-900">No students found</h3>
          <p className="mt-2 text-gray-500">
            {searchQuery
              ? `No students matching "${searchQuery}"`
              : 'There are no students enrolled in your courses yet.'}
          </p>
          <Link href="/professor/students/invite">
            <Button className="mt-4">
              Invite Students
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
