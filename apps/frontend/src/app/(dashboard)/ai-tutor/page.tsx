'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAITutor } from '@/lib/hooks/useAITutor';

type Message = {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
};

type TutorMode = 'default' | 'beginner' | 'advanced' | 'socratic';

export default function AITutorPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [tutorMode, setTutorMode] = useState<TutorMode>('default');
  const [selectedCourse, setSelectedCourse] = useState<string | null>(null);
  const [courses, setCourses] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { isLoading, getTutoringResponse } = useAITutor();

  // Fetch user's courses on mount
  useEffect(() => {
    const fetchCourses = async () => {
      try {
        // This would be replaced with actual API call
        // const response = await courseService.getUserCourses();
        // setCourses(response.data);
        
        // Mock data for now
        setCourses([
          { id: '1', title: 'Introduction to Machine Learning' },
          { id: '2', title: 'Advanced Database Systems' },
          { id: '3', title: 'Web Development with React' },
        ]);
      } catch (error) {
        console.error('Error fetching courses:', error);
      }
    };

    fetchCourses();
  }, []);

  // Add initial welcome message
  useEffect(() => {
    setMessages([
      {
        id: '1',
        content: 'Hello! I\'m your AI tutor. How can I help you with your learning today?',
        role: 'assistant',
        timestamp: new Date(),
      },
    ]);
  }, []);

  // Scroll to bottom of messages when new ones are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    try {
      const response = await getTutoringResponse({
        message: input,
        mode: tutorMode,
        course_id: selectedCourse,
        conversation_history: messages.map(m => ({
          role: m.role,
          content: m.content
        })),
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.data.response,
        role: 'assistant',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error getting AI response:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error. Please try again later.',
        role: 'assistant',
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-3xl font-bold tracking-tight">AI Tutor</h1>
        <div className="flex space-x-2">
          <select
            className="border rounded-md px-3 py-2 text-sm"
            value={tutorMode}
            onChange={(e) => setTutorMode(e.target.value as TutorMode)}
          >
            <option value="default">Default Mode</option>
            <option value="beginner">Beginner Mode</option>
            <option value="advanced">Advanced Mode</option>
            <option value="socratic">Socratic Mode</option>
          </select>
          
          <select
            className="border rounded-md px-3 py-2 text-sm"
            value={selectedCourse || ''}
            onChange={(e) => setSelectedCourse(e.target.value || null)}
          >
            <option value="">All Courses</option>
            {courses.map((course) => (
              <option key={course.id} value={course.id}>
                {course.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      <Card className="flex-grow flex flex-col overflow-hidden">
        <CardHeader className="border-b">
          <CardTitle>Tutoring Session</CardTitle>
        </CardHeader>
        <CardContent className="flex-grow overflow-y-auto p-0">
          <div className="p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${message.role === 'user' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-900'}`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  <div className={`text-xs mt-1 ${message.role === 'user' ? 'text-primary-100' : 'text-gray-500'}`}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </CardContent>
        <div className="p-4 border-t">
          <form onSubmit={handleSendMessage} className="flex space-x-2">
            <Input
              type="text"
              placeholder="Type your question here..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              className="flex-grow"
            />
            <Button type="submit" disabled={isLoading || !input.trim()}>
              {isLoading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Thinking...
                </span>
              ) : (
                'Send'
              )}
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
