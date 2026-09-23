const { createApp, reactive } = Vue;
const { createRouter, createWebHashHistory } = VueRouter;

const routes = [
  { path: "/", component: homePage },
  { path: "/login", component: loginPage },
  { path: "/register", component: registerPage },

  { path: "/admin/dashboard", component: adminDashboard, meta: { role: "admin" } },
  { path: "/admin/treks", component: adminTreks, meta: { role: "admin" } },
  { path: "/admin/people", component: adminPeople, meta: { role: "admin" } },
  { path: "/admin/search", component: adminSearch, meta: { role: "admin" } },

  { path: "/staff/dashboard", component: staffDashboard, meta: { role: "staff" } },
  { path: "/staff/treks/:id", component: staffTrekDetails, meta: { role: "staff" } },

  { path: "/user/dashboard", component: userDashboard, meta: { role: "trekker" } },
  { path: "/user/bookings", component: userBookings, meta: { role: "trekker" } },
  { path: "/user/exports", component: userExports, meta: { role: "trekker" } },
  { path: "/user/profile", component: userProfile, meta: { role: "trekker" } },

  { path: "/:pathMatch(.*)*", redirect: "/" },
];

const router = createRouter({ history: createWebHashHistory(), routes });
router.beforeEach((to) => {
  const user = trek_manager.getUser();
  if (to.meta.role) {
    if (!user) return "/login";
    if (user.role !== to.meta.role) {
      const dest = { admin: "/admin/dashboard", staff: "/staff/dashboard", trekker: "/user/dashboard" }[user.role];
      return dest;
    }
  }
  return true;
});

const App = {
  components: { NavBar },
  setup() {
    const state = reactive({ user: trek_manager.getUser() });
    return { state };
  },
  methods: {
    onLoggedIn(user) { this.state.user = user; },
    logout() {
      trek_manager.clearSession();
      this.state.user = null;
      this.$router.push("/login");
    },
  },
  template: `
    <div class="app-shell">
      <nav-bar :user="state.user" @logout="logout"></nav-bar>
      <main class="app-main">
        <router-view @logged-in="onLoggedIn"></router-view>
      </main>
    </div>
  `,
};

const app = createApp(App);
app.use(router);
app.mount("#app");