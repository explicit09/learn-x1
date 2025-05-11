'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Formik, Form, Field, ErrorMessage } from 'formik';
import * as Yup from 'yup';

import AuthLayout from '@/components/layout/auth-layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/lib/hooks/useAuth';

const LoginSchema = Yup.object().shape({
  email: Yup.string().email('Invalid email address').required('Email is required'),
  password: Yup.string().required('Password is required'),
});

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);

  const handleSubmit = async (values: { email: string; password: string }, { setSubmitting }: any) => {
    try {
      setServerError(null);
      await login(values.email, values.password);
      router.push('/dashboard');
    } catch (error: any) {
      setServerError(error.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout 
      title="Sign in to your account" 
      description="Or create a new account if you don't have one"
    >
      <Formik
        initialValues={{ email: '', password: '' }}
        validationSchema={LoginSchema}
        onSubmit={handleSubmit}
      >
        {({ isSubmitting, errors, touched }) => (
          <Form className="space-y-6">
            {serverError && (
              <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
                <span className="block sm:inline">{serverError}</span>
              </div>
            )}
            
            <div>
              <Field
                as={Input}
                id="email"
                name="email"
                type="email"
                label="Email address"
                autoComplete="email"
                error={touched.email && errors.email ? errors.email : ''}
              />
            </div>

            <div>
              <Field
                as={Input}
                id="password"
                name="password"
                type="password"
                label="Password"
                autoComplete="current-password"
                error={touched.password && errors.password ? errors.password : ''}
              />
              <div className="text-sm mt-2">
                <Link href="/forgot-password" className="font-medium text-primary-600 hover:text-primary-500">
                  Forgot your password?
                </Link>
              </div>
            </div>

            <div>
              <Button
                type="submit"
                className="w-full"
                isLoading={isSubmitting}
              >
                Sign in
              </Button>
            </div>

            <div className="text-center mt-4">
              <p className="text-sm text-gray-600">
                Don't have an account?{' '}
                <Link href="/register" className="font-medium text-primary-600 hover:text-primary-500">
                  Sign up
                </Link>
              </p>
            </div>
          </Form>
        )}
      </Formik>
    </AuthLayout>
  );
}
