export default defineNuxtRouteMiddleware((to, from) => {
  const token = useCookie('auth_token')
  
  // If no token and not going to login page, redirect to login
  if (!token.value && to.path !== '/login') {
    return navigateTo('/login')
  }
  
  // If token and going to login, redirect to home overview
  if (token.value && to.path === '/login') {
    return navigateTo('/')
  }
})
