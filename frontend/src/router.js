import { createRouter, createWebHistory } from 'vue-router'
import { api, getToken } from './api'
import LoginView from './views/LoginView.vue'
import DashboardView from './views/DashboardView.vue'
import RuleDetailView from './views/RuleDetailView.vue'
import AdminPlatformsView from './views/AdminPlatformsView.vue'
import AdminRulesView from './views/AdminRulesView.vue'
import AdminUsersView from './views/AdminUsersView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView, meta: { public: true } },
    { path: '/', component: DashboardView },
    { path: '/rules/:id', component: RuleDetailView, props: true },
    { path: '/admin/platforms', component: AdminPlatformsView, meta: { admin: true } },
    { path: '/admin/rules', component: AdminRulesView, meta: { admin: true } },
    { path: '/admin/users', component: AdminUsersView, meta: { admin: true } },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  if (!getToken()) return '/login'
  if (to.meta.admin) {
    const me = await api.me()
    if (me.role !== 'admin') return '/'
  }
  return true
})

export default router
