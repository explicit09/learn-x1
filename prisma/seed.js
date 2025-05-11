// Prisma seed script for the LEARN-X platform
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  console.log('Starting database seeding...');

  // Clean up existing data if needed
  await cleanDatabase();

  // Create organizations
  const org1 = await prisma.organization.create({
    data: {
      name: 'Demo University',
      domain: 'demo-university.edu'
    }
  });

  const org2 = await prisma.organization.create({
    data: {
      name: 'Tech Academy',
      domain: 'tech-academy.org'
    }
  });

  console.log('Created organizations');

  // Create users with different roles
  const adminUser = await prisma.user.create({
    data: {
      email: 'admin@demo-university.edu',
      name: 'Admin User',
      role: 'ADMIN',
      organizationId: org1.id
    }
  });

  const professor1 = await prisma.user.create({
    data: {
      email: 'professor@demo-university.edu',
      name: 'Professor Smith',
      role: 'PROFESSOR',
      organizationId: org1.id
    }
  });

  const student1 = await prisma.user.create({
    data: {
      email: 'student1@demo-university.edu',
      name: 'John Student',
      role: 'STUDENT',
      organizationId: org1.id,
      learningStyle: {
        create: {
          visualScore: 8,
          auditoryScore: 6,
          readingScore: 7,
          kinestheticScore: 5
        }
      }
    }
  });

  const student2 = await prisma.user.create({
    data: {
      email: 'student2@demo-university.edu',
      name: 'Jane Student',
      role: 'STUDENT',
      organizationId: org1.id,
      learningStyle: {
        create: {
          visualScore: 6,
          auditoryScore: 8,
          readingScore: 7,
          kinestheticScore: 9
        }
      }
    }
  });

  // Create users for the second organization
  const professor2 = await prisma.user.create({
    data: {
      email: 'professor@tech-academy.org',
      name: 'Professor Johnson',
      role: 'PROFESSOR',
      organizationId: org2.id
    }
  });

  const student3 = await prisma.user.create({
    data: {
      email: 'student@tech-academy.org',
      name: 'Tech Student',
      role: 'STUDENT',
      organizationId: org2.id,
      learningStyle: {
        create: {
          visualScore: 9,
          auditoryScore: 5,
          readingScore: 6,
          kinestheticScore: 7
        }
      }
    }
  });

  console.log('Created users');

  // Create courses
  const course1 = await prisma.course.create({
    data: {
      title: 'Introduction to Computer Science',
      description: 'Fundamentals of computer science and programming',
      organizationId: org1.id,
      professorId: professor1.id
    }
  });

  const course2 = await prisma.course.create({
    data: {
      title: 'Advanced Mathematics',
      description: 'Advanced topics in mathematics and statistics',
      organizationId: org1.id,
      professorId: professor1.id
    }
  });

  const course3 = await prisma.course.create({
    data: {
      title: 'Web Development Fundamentals',
      description: 'Introduction to web development technologies',
      organizationId: org2.id,
      professorId: professor2.id
    }
  });

  console.log('Created courses');

  // Create enrollments
  await prisma.enrollment.create({
    data: {
      userId: student1.id,
      courseId: course1.id
    }
  });

  await prisma.enrollment.create({
    data: {
      userId: student1.id,
      courseId: course2.id
    }
  });

  await prisma.enrollment.create({
    data: {
      userId: student2.id,
      courseId: course1.id
    }
  });

  await prisma.enrollment.create({
    data: {
      userId: student3.id,
      courseId: course3.id
    }
  });

  console.log('Created enrollments');

  // Create modules and topics for Course 1
  const module1 = await prisma.module.create({
    data: {
      title: 'Programming Basics',
      description: 'Introduction to programming concepts',
      order: 1,
      courseId: course1.id
    }
  });

  const topic1 = await prisma.topic.create({
    data: {
      title: 'Variables and Data Types',
      description: 'Understanding variables and basic data types',
      order: 1,
      moduleId: module1.id
    }
  });

  const topic2 = await prisma.topic.create({
    data: {
      title: 'Control Structures',
      description: 'Loops and conditional statements',
      order: 2,
      moduleId: module1.id
    }
  });

  console.log('Created modules and topics');

  // Create materials
  const material1 = await prisma.material.create({
    data: {
      title: 'Introduction to Variables',
      description: 'Learn about variables and how they work',
      fileUrl: 'https://storage.example.com/materials/variables.pdf',
      fileType: 'PDF',
      topicId: topic1.id
    }
  });

  // Create content chunks with mock embeddings
  await prisma.contentChunk.create({
    data: {
      content: 'Variables are containers for storing data values. In Python, variables are created when you assign a value to it.',
      materialId: material1.id
    }
  });

  await prisma.contentChunk.create({
    data: {
      content: 'Python has the following data types built-in by default: Text Type (str), Numeric Types (int, float, complex), etc.',
      materialId: material1.id
    }
  });

  console.log('Created materials and content chunks');

  // Create a quiz
  const quiz1 = await prisma.quiz.create({
    data: {
      title: 'Variables and Data Types Quiz',
      description: 'Test your knowledge of variables and data types',
      courseId: course1.id
    }
  });

  // Create questions
  const question1 = await prisma.question.create({
    data: {
      content: 'Which of the following is a valid variable name in Python?',
      type: 'MULTIPLE_CHOICE',
      quizId: quiz1.id,
      options: {
        create: [
          { content: '2variable', isCorrect: false },
          { content: '_variable', isCorrect: true },
          { content: 'variable-name', isCorrect: false },
          { content: 'variable name', isCorrect: false }
        ]
      }
    }
  });

  const question2 = await prisma.question.create({
    data: {
      content: 'What is the result of 5 + "5" in JavaScript?',
      type: 'MULTIPLE_CHOICE',
      quizId: quiz1.id,
      options: {
        create: [
          { content: '10', isCorrect: false },
          { content: '55', isCorrect: true },
          { content: 'Error', isCorrect: false },
          { content: 'undefined', isCorrect: false }
        ]
      }
    }
  });

  console.log('Created quiz and questions');

  // Create a quiz attempt
  const quizAttempt1 = await prisma.quizAttempt.create({
    data: {
      userId: student1.id,
      quizId: quiz1.id,
      score: 0.5,
      completedAt: new Date(),
      answers: {
        create: [
          {
            questionId: question1.id,
            content: '_variable',
            isCorrect: true
          },
          {
            questionId: question2.id,
            content: '10',
            isCorrect: false
          }
        ]
      }
    }
  });

  console.log('Created quiz attempt');

  // Create AI interactions
  await prisma.aIInteraction.create({
    data: {
      userId: student1.id,
      query: 'What is a variable in programming?',
      response: 'A variable is a named storage location that can hold a value. Think of it as a container that holds data which can be changed during program execution.',
      confusionLevel: 2
    }
  });

  await prisma.aIInteraction.create({
    data: {
      userId: student1.id,
      query: 'I don\'t understand data types',
      response: 'Data types specify what kind of data a variable can hold. Common data types include integers (whole numbers), floats (decimal numbers), strings (text), and booleans (true/false values).',
      confusionLevel: 5
    }
  });

  console.log('Created AI interactions');

  // Create analytics events
  await prisma.analyticsEvent.create({
    data: {
      eventType: 'MATERIAL_VIEW',
      userId: student1.id,
      courseId: course1.id,
      materialId: material1.id,
      metadata: { timeSpent: 300, completionPercentage: 100 }
    }
  });

  await prisma.analyticsEvent.create({
    data: {
      eventType: 'QUIZ_COMPLETE',
      userId: student1.id,
      courseId: course1.id,
      quizId: quiz1.id,
      metadata: { score: 0.5, timeSpent: 180 }
    }
  });

  await prisma.analyticsEvent.create({
    data: {
      eventType: 'CONFUSION_DETECTED',
      userId: student1.id,
      courseId: course1.id,
      metadata: { topic: 'data types', level: 5 }
    }
  });

  console.log('Created analytics events');

  console.log('Database seeding completed successfully!');
}

async function cleanDatabase() {
  // Delete data in reverse order of dependencies
  await prisma.analyticsEvent.deleteMany();
  await prisma.questionAnswer.deleteMany();
  await prisma.quizAttempt.deleteMany();
  await prisma.questionOption.deleteMany();
  await prisma.question.deleteMany();
  await prisma.quiz.deleteMany();
  await prisma.aIInteraction.deleteMany();
  await prisma.contentChunk.deleteMany();
  await prisma.material.deleteMany();
  await prisma.topic.deleteMany();
  await prisma.module.deleteMany();
  await prisma.enrollment.deleteMany();
  await prisma.course.deleteMany();
  await prisma.learningStyle.deleteMany();
  await prisma.user.deleteMany();
  await prisma.organization.deleteMany();
}

main()
  .catch((e) => {
    console.error('Error during seeding:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
