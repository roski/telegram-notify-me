import { Clock, User } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'

/**
 * Fixed bottom navigation bar with Timeline and Settings tabs.
 */
export function BottomNav() {
  const navigate = useNavigate()
  const { pathname } = useLocation()

  const tabs = [
    { path: '/', icon: Clock, label: 'Timeline' },
    { path: '/settings', icon: User, label: 'Settings' },
  ]

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-20 bg-white border-t border-gray-100 flex justify-around items-center h-16 px-6 safe-area-inset-bottom">
      {tabs.map(({ path, icon: Icon, label }) => {
        const active = pathname === path
        return (
          <button
            key={path}
            onClick={() => navigate(path)}
            className={cn(
              'flex flex-col items-center gap-1 px-6 py-1 rounded-2xl transition-colors',
              active ? 'text-blue-500' : 'text-gray-400'
            )}
          >
            <Icon size={22} strokeWidth={active ? 2.5 : 1.8} />
            <span className="text-xs font-medium">{label}</span>
          </button>
        )
      })}
    </nav>
  )
}
