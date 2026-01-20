import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import { useAuthStore } from '@/stores/authStore'
import { UpgradeModal } from '@/components/UpgradeModal'

// Layouts
import AppLayout from '@/layouts/AppLayout'
import AuthLayout from '@/layouts/AuthLayout'

// Components
import AdminRoute from '@/components/AdminRoute'

// Pages
import Login from '@/pages/auth/Login'
import Register from '@/pages/auth/Register'
import Dashboard from '@/pages/Dashboard'
import Agents from '@/pages/agents/Agents'
import AgentCreate from '@/pages/agents/AgentCreate'
import AgentEdit from '@/pages/agents/AgentEdit'
import Plans from '@/pages/plans/Plans'
import PlanCreate from '@/pages/plans/PlanCreate'
import Campaigns from '@/pages/campaigns/Campaigns'
import CampaignCreate from '@/pages/campaigns/CampaignCreate'
import CampaignDetail from '@/pages/campaigns/CampaignDetail'
import Leads from '@/pages/Leads'
import Admin from '@/pages/admin/Admin'
import Upgrade from '@/pages/Upgrade'
import Settings from '@/pages/Settings'

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

// Public Route Component (redirect if authenticated)
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }
  
  return <>{children}</>
}

function App() {
  return (
    <>
      <Routes>
        {/* Public Routes */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          } />
          <Route path="/register" element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          } />
        </Route>

        {/* Protected Routes */}
        <Route element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }>
          <Route path="/dashboard" element={<Dashboard />} />
          
          {/* Agents */}
          <Route path="/agents" element={<Agents />} />
          <Route path="/agents/new" element={<AgentCreate />} />
          <Route path="/agents/:id/edit" element={<AgentEdit />} />
          
          {/* Plans - Admin Only */}
          <Route path="/plans" element={
            <AdminRoute>
              <Plans />
            </AdminRoute>
          } />
          <Route path="/plans/new" element={
            <AdminRoute>
              <PlanCreate />
            </AdminRoute>
          } />
          
          {/* Campaigns */}
          <Route path="/campaigns" element={<Campaigns />} />
          <Route path="/campaigns/new" element={<CampaignCreate />} />
          <Route path="/campaigns/:id" element={<CampaignDetail />} />
          
          {/* Leads */}
          <Route path="/prospects" element={<Leads />} />
          
          {/* Upgrade */}
          <Route path="/upgrade" element={<Upgrade />} />
          
          {/* Settings */}
          <Route path="/settings" element={<Settings />} />
          
          {/* Admin - Admin Only */}
          <Route path="/admin" element={
            <AdminRoute>
              <Admin />
            </AdminRoute>
          } />
        </Route>

        {/* Redirect root to dashboard or login */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* 404 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
      
      <Toaster />
      <UpgradeModal />
    </>
  )
}

export default App
