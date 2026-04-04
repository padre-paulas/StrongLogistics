import { useForm } from 'react-hook-form';
import { useAuth } from '../context/AuthContext';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import type { Role } from '../types';

interface LoginForm {
  email: string;
  role: Role;
}

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { isSubmitting, errors } } = useForm<LoginForm>({
    defaultValues: { role: 'driver' },
  });

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const onSubmit = async (data: LoginForm) => {
    await login(data.email, data.role);
    navigate('/dashboard', { replace: true });
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">🚚 StrongLogistics</h1>
          <p className="text-gray-500 mt-2">Logistics Dashboard</p>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              {...register('email', { required: 'Email is required' })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="you@company.com"
            />
            {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
            <select
              {...register('role', { required: 'Role is required' })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="driver">Driver</option>
              <option value="dispatcher">Dispatcher</option>
              <option value="admin">Admin</option>
            </select>
            {errors.role && <p className="text-red-500 text-xs mt-1">{errors.role.message}</p>}
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            {isSubmitting ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <p className="text-center text-sm text-gray-500 mt-6">
          Don't have an account?{' '}
          <Link to="/signup" className="text-blue-600 hover:underline font-medium">
            Sign Up
          </Link>
        </p>
      </div>
    </div>
  );
}
