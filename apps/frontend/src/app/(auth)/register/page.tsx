'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Formik, Form, Field, ErrorMessage } from 'formik';
import * as Yup from 'yup';

import AuthLayout from '@/components/layout/auth-layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { authService } from '@/lib/api';

const RegisterSchema = Yup.object().shape({
  name: Yup.string().required('Name is required'),
  email: Yup.string().email('Invalid email address').required('Email is required'),
  password: Yup.string()
    .min(8, 'Password must be at least 8 characters')
    .required('Password is required'),
  organization_name: Yup.string().required('Organization name is required'),
  organization_domain: Yup.string(),
});

export default function RegisterPage() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);

  const handleSubmit = async (values: any, { setSubmitting }: any) => {
    try {
      setServerError(null);
      await authService.register(values);
      router.push('/login?registered=true');
    } catch (error: any) {
      setServerError(error.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout 
      title="Create your account" 
      description="Join LEARN-X to start your learning journey"
    >
      <Formik
        initialValues={{
          name: '',
          email: '',
          password: '',
          organization_name: '',
          organization_domain: '',
        }}
        validationSchema={RegisterSchema}
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
                id="name"
                name="name"
                type="text"
                label="Full name"
                autoComplete="name"
                error={touched.name && errors.name ? errors.name : ''}
              />
            </div>

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
                autoComplete="new-password"
                error={touched.password && errors.password ? errors.password : ''}
              />
            </div>

            <div>
              <Field
                as={Input}
                id="organization_name"
                name="organization_name"
                type="text"
                label="Organization name"
                error={touched.organization_name && errors.organization_name ? errors.organization_name : ''}
              />
            </div>

            <div>
              <Field
                as={Input}
                id="organization_domain"
                name="organization_domain"
                type="text"
                label="Organization domain (optional)"
                helperText="e.g., example.com"
                error={touched.organization_domain && errors.organization_domain ? errors.organization_domain : ''}
              />
            </div>

            <div>
              <Button
                type="submit"
                className="w-full"
                isLoading={isSubmitting}
              >
                Sign up
              </Button>
            </div>

            <div className="text-center mt-4">
              <p className="text-sm text-gray-600">
                Already have an account?{' '}
                <Link href="/login" className="font-medium text-primary-600 hover:text-primary-500">
                  Sign in
                </Link>
              </p>
            </div>
          </Form>
        )}
      </Formik>
    </AuthLayout>
  );
}
