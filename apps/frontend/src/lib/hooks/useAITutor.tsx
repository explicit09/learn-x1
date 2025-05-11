'use client';

import { createContext, useContext, useState, ReactNode } from 'react';
import { aiService } from '@/lib/api';

type TutorMode = 'default' | 'beginner' | 'advanced' | 'socratic';

type TutoringRequest = {
  message: string;
  mode: TutorMode;
  course_id?: string | null;
  conversation_history: { role: 'user' | 'assistant'; content: string }[];
};

type AITutorContextType = {
  isLoading: boolean;
  getTutoringResponse: (request: TutoringRequest) => Promise<any>;
};

const AITutorContext = createContext<AITutorContextType | undefined>(undefined);

export function AITutorProvider({ children }: { children: ReactNode }) {
  const [isLoading, setIsLoading] = useState(false);

  const getTutoringResponse = async (request: TutoringRequest) => {
    setIsLoading(true);
    try {
      // In a real implementation, this would call the actual API
      // return await aiService.getTutoringResponse(request);
      
      // Mock response for now
      await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate network delay
      
      return {
        data: {
          response: generateMockResponse(request.message, request.mode),
        }
      };
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to generate mock responses based on the tutoring mode
  const generateMockResponse = (message: string, mode: TutorMode) => {
    const lowerMessage = message.toLowerCase();
    
    // Basic response patterns based on mode
    if (mode === 'beginner') {
      if (lowerMessage.includes('vector')) {
        return "Vectors are a way to represent data in a format that computers can understand and compare. Think of them like coordinates on a map - they help the AI understand where different pieces of information are in relation to each other. In the context of AI, we convert text, images, or other data into these 'coordinates' (vectors) so the AI can work with them.";
      } else if (lowerMessage.includes('database') || lowerMessage.includes('sql')) {
        return "A database is like a digital filing cabinet where we store information in an organized way. SQL (Structured Query Language) is the language we use to talk to many databases - it helps us add, find, change, or remove information. Imagine if you could ask your filing cabinet questions like 'show me all the blue folders from last year' - that's what SQL lets us do with data!";
      }
    } else if (mode === 'advanced') {
      if (lowerMessage.includes('vector')) {
        return "Vector embeddings in the context of AI represent semantic meaning in a high-dimensional space. When we generate embeddings using models like OpenAI's text-embedding-ada-002, we're mapping text to points in a vector space where semantic similarity corresponds to geometric proximity. This allows for efficient similarity search using techniques like cosine similarity or approximate nearest neighbors algorithms such as HNSW or IVF. In our implementation with pgvector, we're storing these high-dimensional vectors (typically 1536 dimensions for OpenAI embeddings) in PostgreSQL and leveraging specialized indexes for efficient retrieval.";
      } else if (lowerMessage.includes('database') || lowerMessage.includes('sql')) {
        return "Our implementation uses PostgreSQL with the pgvector extension for vector similarity search. We've implemented Row-Level Security (RLS) policies to enforce multi-tenant isolation at the database level, ensuring that queries only return data belonging to the authenticated user's organization. The schema includes materialized views for analytics queries to improve performance, and we've implemented query optimization techniques including proper indexing strategies, query plan analysis, and connection pooling to handle concurrent requests efficiently.";
      }
    } else if (mode === 'socratic') {
      if (lowerMessage.includes('vector')) {
        return "That's an interesting question about vectors. Before we dive in, what do you already understand about vector embeddings? And what specific aspect of vector embeddings are you trying to understand better?";
      } else if (lowerMessage.includes('database') || lowerMessage.includes('sql')) {
        return "Good question about databases. Let's explore this together. What database systems have you worked with before? And what specific challenges are you facing with your database implementation?";
      }
    }
    
    // Default response if no specific pattern is matched
    return "That's an interesting question! I'd be happy to help you understand this topic better. Could you provide a bit more context about what you're trying to learn, and I'll tailor my explanation to your needs?";
  };

  return (
    <AITutorContext.Provider
      value={{
        isLoading,
        getTutoringResponse,
      }}
    >
      {children}
    </AITutorContext.Provider>
  );
}

export function useAITutor() {
  const context = useContext(AITutorContext);
  if (context === undefined) {
    throw new Error('useAITutor must be used within an AITutorProvider');
  }
  return context;
}
