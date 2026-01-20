import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

interface AdminRouteProps {
  children?: React.ReactNode
}

export default function AdminRoute({ children }: AdminRouteProps) {
  const { isAdmin, isAuthenticated } = useAuthStore()

  // Se não está autenticado, redireciona para login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // Se não é admin, redireciona para dashboard com mensagem
  if (!isAdmin()) {
    return <Navigate to="/dashboard" replace state={{ error: 'Acesso restrito a administradores' }} />
  }

  // Se é admin, renderiza o conteúdo
  return children ? <>{children}</> : <Outlet />
}
