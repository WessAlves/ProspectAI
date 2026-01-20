import { useState } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Bot, 
  FileText, 
  Megaphone, 
  Users, 
  Menu, 
  X,
  LogOut,
  Shield,
  Settings,
  AlertCircle,
  Zap
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/lib/utils'

interface NavItem {
  name: string
  href: string
  icon: typeof LayoutDashboard
  adminOnly?: boolean
}

const navigationItems: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Agentes', href: '/agents', icon: Bot },
  { name: 'Planos', href: '/plans', icon: FileText, adminOnly: true },
  { name: 'Campanhas', href: '/campaigns', icon: Megaphone },
  { name: 'Leads', href: '/prospects', icon: Users },
  { name: 'Administração', href: '/admin', icon: Shield, adminOnly: true },
]

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout, isAdmin } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Filtra itens de navegação baseado no perfil do usuário
  const navigation = navigationItems.filter(item => {
    if (item.adminOnly) {
      return isAdmin()
    }
    return true
  })

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        "fixed inset-y-0 left-0 z-50 w-64 bg-card border-r transform transition-transform duration-200 ease-in-out lg:translate-x-0",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-4 border-b">
            <Link to="/dashboard" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-lg">P</span>
              </div>
              <span className="font-bold text-xl">ProspectAI</span>
            </Link>
            <Button 
              variant="ghost" 
              size="icon" 
              className="lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href || 
                location.pathname.startsWith(item.href + '/')
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    "flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive 
                      ? "bg-primary text-primary-foreground" 
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </nav>

          {/* User section */}
          <div className="p-4 border-t">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                  <span className="text-primary font-medium text-sm">
                    {user?.full_name?.charAt(0).toUpperCase() || 'U'}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium truncate">{user?.full_name}</p>
                    {isAdmin() && (
                      <span className="px-1.5 py-0.5 bg-amber-100 text-amber-800 text-[10px] font-semibold rounded">
                        ADMIN
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Button 
                  variant="ghost" 
                  size="icon" 
                  onClick={() => navigate('/settings')}
                  title="Configurações"
                >
                  <Settings className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" onClick={handleLogout} title="Sair">
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 h-16 bg-background/95 backdrop-blur border-b flex items-center px-4 lg:px-6">
          <Button 
            variant="ghost" 
            size="icon" 
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>
          
          <div className="flex-1" />
          
          {/* Plan badge and upgrade button */}
          <div className="flex items-center space-x-3">
            <span className={cn(
              "px-2 py-1 rounded-full text-xs font-medium",
              user?.plan_tier === 'free' && "bg-gray-100 text-gray-800",
              user?.plan_tier === 'starter' && "bg-blue-100 text-blue-800",
              user?.plan_tier === 'pro' && "bg-purple-100 text-purple-800",
              user?.plan_tier === 'scale' && "bg-gradient-to-r from-amber-100 to-orange-100 text-orange-800"
            )}>
              {user?.plan_tier?.toUpperCase() || 'FREE'}
            </span>
            
            {user?.plan_tier !== 'scale' && (
              <Button
                size="sm"
                onClick={() => navigate('/upgrade')}
                className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white gap-1.5"
              >
                <Zap className="h-3.5 w-3.5" />
                Upgrade
              </Button>
            )}
          </div>
        </header>

        {/* Banner de cadastro incompleto */}
        {user && !user.profile_completed && location.pathname !== '/settings' && (
          <div className="bg-amber-50 border-b border-amber-200 px-4 py-3 lg:px-6">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-amber-800">
                    Complete seu cadastro
                  </p>
                  <p className="text-xs text-amber-700">
                    Preencha seus dados pessoais para aproveitar todos os recursos da plataforma.
                  </p>
                </div>
              </div>
              <Button
                size="sm"
                variant="outline"
                className="border-amber-300 text-amber-800 hover:bg-amber-100 flex-shrink-0"
                onClick={() => navigate('/settings')}
              >
                Completar agora
              </Button>
            </div>
          </div>
        )}

        {/* Page content */}
        <main className="p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
