const NavBar = {
  props: ["user"],
  emits: ["logout"],
  template: `
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3 mb-4">
      <router-link class="navbar-brand fw-bold" to="/">
        <i class="bi bi-flag-fill me-1"></i> Trek Manager
      </router-link>
      <div class="collapse navbar-collapse show">
        <ul class="navbar-nav me-auto" v-if="user">
          <template v-if="user.role === 'admin'">
            <li class="nav-item"><router-link class="nav-link" to="/admin/dashboard">Dashboard</router-link></li>
            <li class="nav-item"><router-link class="nav-link" to="/admin/treks">Treks</router-link></li>
            <li class="nav-item"><router-link class="nav-link" to="/admin/people">People</router-link></li>
            <li class="nav-item"><router-link class="nav-link" to="/admin/search">Search</router-link></li>
          </template>
          <template v-else-if="user.role === 'staff'">
            <li class="nav-item"><router-link class="nav-link" to="/staff/dashboard">My Treks</router-link></li>
          </template>
          <template v-else-if="user.role === 'trekker'">
            <li class="nav-item"><router-link class="nav-link" to="/user/dashboard">Browse Treks</router-link></li>
            <li class="nav-item"><router-link class="nav-link" to="/user/bookings">My Bookings</router-link></li>
            <li class="nav-item"><router-link class="nav-link" to="/user/exports">Export History</router-link></li>
            <li class="nav-item"><router-link class="nav-link" to="/user/profile">Profile</router-link></li>
          </template>
        </ul>
        <span class="navbar-text text-white me-3" v-if="user">
          <i class="bi bi-person-circle me-1"></i>{{ user.full_name }} <span class="badge bg-secondary text-capitalize">{{ user.role }}</span>
        </span>
        <button v-if="user" class="btn btn-outline-light btn-sm" @click="$emit('logout')">Log out</button>
      </div>
    </nav>`,
};

const homePage = {
  template: `
    <div class="container text-center py-5">
      <i class="bi bi-flag-fill display-1 text-success"></i>
      <h1 class="mt-3">Welcome to Trek Manager</h1>
      <p class="lead text-muted">Discover, book, and manage trekking adventures.</p>
      <router-link to="/login" class="btn btn-success btn-lg me-2">Log In</router-link>
      <router-link to="/register" class="btn btn-outline-success btn-lg">Register</router-link>
    </div>`,
};

const loginPage = {
  emits: ["logged-in"],
  data() { return { email: "", password: "", error: "", loading: false }; },
  methods: {
    async submit() {
      this.error = ""; this.loading = true;
      try {
        const data = await trek_manager.post("/auth/login", { email: this.email, password: this.password });
        trek_manager.setSession(data.access_token, data.user);
        this.$emit("logged-in", data.user);
        const dest = { admin: "/admin/dashboard", staff: "/staff/dashboard", trekker: "/user/dashboard" }[data.user.role];
        this.$router.push(dest);
      } catch (e) { this.error = e.message; }
      finally { this.loading = false; }
    },
  },
  template: `
    <div class="container" style="max-width:420px;">
      <div class="card shadow-sm mt-5">
        <div class="card-body p-4">
          <h3 class="card-title mb-3 text-center">Log In</h3>
          <div class="alert alert-danger py-2" v-if="error">{{ error }}</div>
          <form @submit.prevent="submit">
            <div class="mb-3">
              <label class="form-label">Email</label>
              <input v-model="email" type="email" class="form-control" required>
            </div>
            <div class="mb-3">
              <label class="form-label">Password</label>
              <input v-model="password" type="password" class="form-control" required>
            </div>
            <button class="btn btn-success w-100" :disabled="loading">
              {{ loading ? "Logging in..." : "Log In" }}
            </button>
          </form>
          <p class="text-center mt-3 mb-0">
            No account? <router-link to="/register">Register</router-link>
          </p>
        </div>
      </div>
    </div>`,
};

const registerPage = {
  data() {
    return { fullName: "", email: "", phone: "", password: "", confirm: "",
             role: "trekker", error: "", success: "", loading: false };
  },
  methods: {
    async submit() {
      this.error = ""; this.success = "";
      if (this.password !== this.confirm) { this.error = "Passwords do not match."; return; }
      this.loading = true;
      try {
        const data = await trek_manager.post("/auth/register", {
          fullName: this.fullName, email: this.email, phone: this.phone,
          password: this.password, role: this.role,
        });
        this.success = data.message;
      } catch (e) {
        this.error = e.fields ? Object.values(e.fields).join(" ") : e.message;
      } finally { this.loading = false; }
    },
  },
  template: `
    <div class="container" style="max-width:480px;">
      <div class="card shadow-sm mt-5">
        <div class="card-body p-4">
          <h3 class="card-title mb-3 text-center">Register</h3>
          <div class="alert alert-danger py-2" v-if="error">{{ error }}</div>
          <div class="alert alert-success py-2" v-if="success">
            {{ success }} <router-link to="/login">Go to login</router-link>
          </div>
          <form @submit.prevent="submit" v-if="!success">
            <div class="mb-3">
              <label class="form-label">I am registering as</label>
              <select v-model="role" class="form-select">
                <option value="trekker">User (Trekker)</option>
                <option value="staff">Trek Staff (requires Admin approval)</option>
              </select>
            </div>
            <div class="mb-3"><label class="form-label">Full Name</label>
              <input v-model="fullName" class="form-control" required></div>
            <div class="mb-3"><label class="form-label">Email</label>
              <input v-model="email" type="email" class="form-control" required></div>
            <div class="mb-3"><label class="form-label">Phone (optional)</label>
              <input v-model="phone" class="form-control"></div>
            <div class="mb-3"><label class="form-label">Password</label>
              <input v-model="password" type="password" class="form-control" required minlength="6"></div>
            <div class="mb-3"><label class="form-label">Confirm Password</label>
              <input v-model="confirm" type="password" class="form-control" required minlength="6"></div>
            <button class="btn btn-success w-100" :disabled="loading">
              {{ loading ? "Creating account..." : "Register" }}
            </button>
          </form>
        </div>
      </div>
    </div>`,
};

const adminDashboard = {
  data() { return { stats: {}, recent: [], loading: true }; },
  async created() {
    const data = await trek_manager.get("/admin/dashboard");
    this.stats = data.stats; this.recent = data.recent_bookings; this.loading = false;
  },
  template: `
    <div class="container">
      <h2 class="mb-4">Admin Dashboard</h2>
      <div class="row g-3 mb-4">
        <div class="col-md-2 col-6" v-for="(v,k) in stats" :key="k">
          <div class="card text-center shadow-sm h-100">
            <div class="card-body">
              <div class="display-6">{{ v }}</div>
              <div class="text-muted small text-capitalize">{{ k.replaceAll('_',' ') }}</div>
            </div>
          </div>
        </div>
      </div>
      <h5>Recent Bookings</h5>
      <table class="table table-sm table-striped bg-white">
        <thead><tr><th>Trek</th><th>Location</th><th>Status</th><th>Date</th></tr></thead>
        <tbody>
          <tr v-for="b in recent" :key="b.id">
            <td>{{ b.trek_name }}</td><td>{{ b.location }}</td>
            <td><span class="badge bg-info">{{ b.status }}</span></td>
            <td>{{ new Date(b.bookingDate).toLocaleString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>`,
};

const adminTreks = {
  data() {
    return {
      treks: [], staff: [], showModal: false, editing: null, error: "",
      form: { name: "", location: "", difficulty: "Easy", durationOfDays: 1,
              totalSlots: 10, startDate: "", endDate: "", description: "" },
    };
  },
  async created() { await this.refresh(); },
  methods: {
    async refresh() {
      const [t, s] = await Promise.all([trek_manager.get("/admin/treks"), trek_manager.get("/admin/staff")]);
      this.treks = t.treks;
      this.staff = s.staff.filter(x => x.status === "Approved");
    },
    openNew() {
      this.editing = null; this.error = "";
      this.form = { name: "", location: "", difficulty: "Easy", durationOfDays: 1,
                    totalSlots: 10, startDate: "", endDate: "", description: "" };
      this.showModal = true;
    },
    openEdit(t) {
      this.editing = t; this.error = "";
      this.form = { name: t.name, location: t.location, difficulty: t.difficulty,
                    durationOfDays: t.durationOfDays, totalSlots: t.totalSlots,
                    startDate: t.startDate, endDate: t.endDate,
                    description: t.description || "" };
      this.showModal = true;
    },
    async save() {
      this.error = "";
      try {
        if (this.editing) await trek_manager.put(`/admin/treks/${this.editing.id}`, this.form);
        else await trek_manager.post("/admin/treks", this.form);
        this.showModal = false;
        await this.refresh();
      } catch (e) {
        this.error = e.fields ? Object.values(e.fields).join(" ") : e.message;
      }
    },
    async remove(t) {
      if (!confirm(`Delete trek '${t.name}'?`)) return;
      await trek_manager.del(`/admin/treks/${t.id}`);
      await this.refresh();
    },
    async assign(t) {
      const staffId = prompt(
        "Assign staff - enter staff ID:\n" + this.staff.map(s => `${s.id}: ${s.fullName}`).join("\n")
      );
      if (!staffId) return;
      try {
        await trek_manager.post(`/admin/treks/${t.id}/assign`, { staffId: parseInt(staffId) });
        await this.refresh();
      } catch (e) { alert(e.message); }
    },
  },
  template: `
    <div class="container">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h2>Treks</h2>
        <button class="btn btn-success" @click="openNew"><i class="bi bi-plus-lg"></i> New Trek</button>
      </div>
      <table class="table table-striped bg-white shadow-sm">
        <thead><tr>
          <th>Name</th><th>Location</th><th>Difficulty</th><th>Slots</th>
          <th>Status</th><th>Staff</th><th>Dates</th><th></th>
        </tr></thead>
        <tbody>
          <tr v-for="t in treks" :key="t.id">
            <td>{{ t.name }}</td><td>{{ t.location }}</td><td>{{ t.difficulty }}</td>
            <td>{{ t.slotsAvailable }}/{{ t.totalSlots }}</td>
            <td><span class="badge bg-secondary">{{ t.status }}</span></td>
            <td>{{ t.staff_name || '—' }}</td>
            <td>{{ t.startDate }} → {{ t.endDate }}</td>
            <td class="text-nowrap">
              <button class="btn btn-sm btn-outline-primary me-1" @click="openEdit(t)">Edit</button>
              <button class="btn btn-sm btn-outline-secondary me-1" @click="assign(t)">Assign</button>
              <button class="btn btn-sm btn-outline-danger" @click="remove(t)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="modal-backdrop-custom" v-if="showModal" @click.self="showModal=false">
        <div class="card shadow modal-card">
          <div class="card-body">
            <h5>{{ editing ? 'Edit Trek' : 'New Trek' }}</h5>
            <div class="alert alert-danger py-2" v-if="error">{{ error }}</div>
            <form @submit.prevent="save">
              <div class="row g-2">
                <div class="col-md-6"><label class="form-label">Name</label><input v-model="form.name" class="form-control" required></div>
                <div class="col-md-6"><label class="form-label">Location</label><input v-model="form.location" class="form-control" required></div>
                <div class="col-md-4"><label class="form-label">Difficulty</label>
                  <select v-model="form.difficulty" class="form-select">
                    <option>Easy</option><option>Moderate</option><option>Hard</option>
                  </select>
                </div>
                <div class="col-md-4"><label class="form-label">Duration (days)</label><input type="number" min="1" v-model.number="form.durationOfDays" class="form-control" required></div>
                <div class="col-md-4"><label class="form-label">Total Slots</label><input type="number" min="1" v-model.number="form.totalSlots" class="form-control" required></div>
                <div class="col-md-6"><label class="form-label">Start Date</label><input type="date" v-model="form.startDate" class="form-control" required></div>
                <div class="col-md-6"><label class="form-label">End Date</label><input type="date" v-model="form.endDate" class="form-control" required></div>
                <div class="col-12"><label class="form-label">Description</label><textarea v-model="form.description" class="form-control" rows="3"></textarea></div>
              </div>
              <div class="mt-3 text-end">
                <button type="button" class="btn btn-outline-secondary me-2" @click="showModal=false">Cancel</button>
                <button class="btn btn-success">Save</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>`,
};

const adminPeople = {
  data() { return { tab: "staff", staff: [], trekkers: [] }; },
  async created() { await this.refresh(); },
  methods: {
    async refresh() {
      const [s, t] = await Promise.all([trek_manager.get("/admin/staff"), trek_manager.get("/admin/trekkers")]);
      this.staff = s.staff; this.trekkers = t.trekkers;
    },
    async approve(u) { await trek_manager.post(`/admin/staff/${u.id}/approve`); await this.refresh(); },
    async blacklist(u) { await trek_manager.post(`/admin/users/${u.id}/blacklist`); await this.refresh(); },
    async reinstate(u) { await trek_manager.post(`/admin/users/${u.id}/reinstate`); await this.refresh(); },
  },
  template: `
    <div class="container">
      <h2 class="mb-3">People</h2>
      <ul class="nav nav-tabs mb-3">
        <li class="nav-item"><a class="nav-link" :class="{active: tab==='staff'}" href="#" @click.prevent="tab='staff'">Trek Staff</a></li>
        <li class="nav-item"><a class="nav-link" :class="{active: tab==='trekkers'}" href="#" @click.prevent="tab='trekkers'">Trekkers</a></li>
      </ul>
      <table class="table table-striped bg-white shadow-sm">
        <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Status</th><th></th></tr></thead>
        <tbody>
          <tr v-for="u in (tab==='staff'?staff:trekkers)" :key="u.id">
            <td>{{ u.id }}</td><td>{{ u.fullName }}</td><td>{{ u.email }}</td><td>{{ u.phone || '—' }}</td>
            <td><span class="badge" :class="u.status==='Blacklisted'?'bg-danger':(u.status==='Pending'?'bg-warning text-dark':'bg-success')">{{ u.status }}</span></td>
            <td class="text-nowrap">
              <button v-if="tab==='staff' && u.status==='Pending'" class="btn btn-sm btn-success me-1" @click="approve(u)">Approve</button>
              <button v-if="u.status!=='Blacklisted'" class="btn btn-sm btn-outline-danger me-1" @click="blacklist(u)">Blacklist</button>
              <button v-if="u.status==='Blacklisted'" class="btn btn-sm btn-outline-success" @click="reinstate(u)">Reinstate</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>`,
};

const adminSearch = {
  data() { return { q: "", category: "treks", results: [], searched: false }; },
  methods: {
    async search() {
      const data = await trek_manager.get(`/admin/search?q=${encodeURIComponent(this.q)}&category=${this.category}`);
      this.results = data.results;
      this.searched = true;
    },
  },
  template: `
    <div class="container">
      <h2 class="mb-3">Search</h2>
      <form class="row g-2 mb-3" @submit.prevent="search">
        <div class="col-auto">
          <select v-model="category" class="form-select">
            <option value="treks">Treks</option>
            <option value="staff">Staff</option>
            <option value="trekkers">Trekkers</option>
          </select>
        </div>
        <div class="col-auto"><input v-model="q" class="form-control" placeholder="Search by name, email, location, or ID"></div>
        <div class="col-auto"><button class="btn btn-success">Search</button></div>
      </form>

      <table class="table table-striped bg-white shadow-sm" v-if="category==='treks'">
        <thead><tr><th>ID</th><th>Name</th><th>Location</th><th>Difficulty</th><th>Status</th></tr></thead>
        <tbody>
          <tr v-for="r in results" :key="r.id">
            <td>{{ r.id }}</td><td>{{ r.name }}</td><td>{{ r.location }}</td><td>{{ r.difficulty }}</td><td>{{ r.status }}</td>
          </tr>
        </tbody>
      </table>
      <table class="table table-striped bg-white shadow-sm" v-else>
        <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Status</th></tr></thead>
        <tbody>
          <tr v-for="r in results" :key="r.id">
            <td>{{ r.id }}</td><td>{{ r.fullName }}</td><td>{{ r.email }}</td><td>{{ r.status }}</td>
          </tr>
        </tbody>
      </table>
      <div class="alert alert-info" v-if="searched && !results.length">No matches found.</div>
    </div>`,
};

const staffDashboard = {
  data() { return { treks: [] }; },
  async created() { const d = await trek_manager.get("/staff/dashboard"); this.treks = d.treks; },
  template: `
    <div class="container">
      <h2 class="mb-3">My Assigned Treks</h2>
      <div class="alert alert-info" v-if="!treks.length">No treks assigned yet.</div>
      <div class="row g-3">
        <div class="col-md-4" v-for="t in treks" :key="t.id">
          <div class="card shadow-sm h-100">
            <div class="card-body">
              <h5>{{ t.name }}</h5>
              <p class="mb-1 text-muted">{{ t.location }} • {{ t.difficulty }}</p>
              <p class="mb-1">Slots: {{ t.slotsAvailable }}/{{ t.totalSlots }}</p>
              <p class="mb-1">Registered users: {{ t.registered_users }}</p>
              <span class="badge bg-secondary">{{ t.status }}</span>
              <div class="mt-2">
                <router-link class="btn btn-sm btn-success" :to="'/staff/treks/' + t.id">Manage</router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>`,
};

const staffTrekDetails = {
  data() { return { trek: null, participants: [], form: { status: "Open", slotsAvailable: 0 }, msg: "" }; },
  async created() { await this.refresh(); },
  methods: {
    async refresh() {
      const id = this.$route.params.id;
      const d = await trek_manager.get(`/staff/treks/${id}`);
      this.trek = d.trek; this.participants = d.participants;
      this.form = { status: this.trek.status === 'Approved' ? 'Open' : this.trek.status, slotsAvailable: this.trek.slotsAvailable };
    },
    async save() {
      const id = this.$route.params.id;
      const d = await trek_manager.put(`/staff/treks/${id}`, this.form);
      this.trek = d.trek; this.msg = d.message;
      await this.refresh();
    },
  },
  template: `
    <div class="container" v-if="trek">
      <router-link to="/staff/dashboard">&larr; Back</router-link>
      <h2 class="mt-2">{{ trek.name }}</h2>
      <p class="text-muted">{{ trek.location }} • {{ trek.difficulty }} • {{ trek.durationOfDays }} day(s)</p>
      <div class="alert alert-success py-2" v-if="msg">{{ msg }}</div>
      <div class="row">
        <div class="col-md-5">
          <div class="card shadow-sm p-3 mb-3">
            <h6>Update Trek</h6>
            <div class="mb-2">
              <label class="form-label">Status</label>
              <select v-model="form.status" class="form-select">
                <option>Open</option><option>Closed</option><option>Completed</option>
              </select>
            </div>
            <div class="mb-2">
              <label class="form-label">Available Slots (max {{ trek.totalSlots }})</label>
              <input type="number" min="0" :max="trek.totalSlots" v-model.number="form.slotsAvailable" class="form-control">
            </div>
            <button class="btn btn-success" @click="save">Update</button>
          </div>
        </div>
        <div class="col-md-7">
          <h6>Registered Participants ({{ participants.length }})</h6>
          <table class="table table-sm table-striped bg-white">
            <thead><tr><th>User</th><th>Status</th><th>Booked On</th></tr></thead>
            <tbody>
              <tr v-for="p in participants" :key="p.id">
                <td>#{{ p.user_id }}</td><td>{{ p.status }}</td><td>{{ new Date(p.bookingDate).toLocaleDateString() }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>`,
};

const userDashboard = {
  data() { return { treks: [], search: "", difficulty: "" }; },
  async created() { await this.refresh(); },
  methods: {
    async refresh() {
      const params = new URLSearchParams({ search: this.search, difficulty: this.difficulty });
      const d = await trek_manager.get(`/user/treks?${params.toString()}`);
      this.treks = d.treks;
    },
    async book(t) {
      try {
        const d = await trek_manager.post(`/user/treks/${t.id}/book`);
        alert(d.message);
        await this.refresh();
      } catch (e) { alert(e.message); }
    },
  },
  template: `
    <div class="container">
      <h2 class="mb-3">Browse Treks</h2>
      <form class="row g-2 mb-3" @submit.prevent="refresh">
        <div class="col-md-4"><input v-model="search" class="form-control" placeholder="Search by name or location"></div>
        <div class="col-md-3">
          <select v-model="difficulty" class="form-select">
            <option value="">All difficulties</option>
            <option>Easy</option><option>Moderate</option><option>Hard</option>
          </select>
        </div>
        <div class="col-auto"><button class="btn btn-success">Filter</button></div>
      </form>
      <div class="row g-3">
        <div class="col-md-4" v-for="t in treks" :key="t.id">
          <div class="card shadow-sm h-100">
            <div class="card-body">
              <h5>{{ t.name }}</h5>
              <p class="mb-1 text-muted">{{ t.location }} • {{ t.difficulty }} • {{ t.durationOfDays }}d</p>
              <p class="mb-1">Slots left: {{ t.slotsAvailable }}</p>
              <p class="mb-1 small text-muted">{{ t.startDate }} → {{ t.endDate }}</p>
              <button class="btn btn-sm btn-success" :disabled="t.slotsAvailable<=0" @click="book(t)">
                {{ t.slotsAvailable<=0 ? 'Full' : 'Book Now' }}
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="alert alert-info mt-3" v-if="!treks.length">No open treks match your search.</div>
    </div>`,
};

const userBookings = {
  data() { return { active: [], completed: [], cancelled: [] }; },
  async created() { await this.refresh(); },
  methods: {
    async refresh() {
      const d = await trek_manager.get("/user/bookings");
      this.active = d.active; this.completed = d.completed; this.cancelled = d.cancelled;
    },
    async cancel(b) {
      if (!confirm("Cancel this booking?")) return;
      await trek_manager.post(`/user/bookings/${b.id}/cancel`);
      await this.refresh();
    },
  },
  template: `
    <div class="container">
      <h2 class="mb-3">My Bookings</h2>
      <h6>Active</h6>
      <table class="table table-sm bg-white shadow-sm mb-4">
        <thead><tr><th>Trek</th><th>Location</th><th>Dates</th><th></th></tr></thead>
        <tbody>
          <tr v-for="b in active" :key="b.id">
            <td>{{ b.trek_name }}</td><td>{{ b.location }}</td><td>{{ b.startDate }} → {{ b.endDate }}</td>
            <td><button class="btn btn-sm btn-outline-danger" @click="cancel(b)">Cancel</button></td>
          </tr>
        </tbody>
      </table>
      <h6>Completed</h6>
      <table class="table table-sm bg-white shadow-sm mb-4">
        <tbody><tr v-for="b in completed" :key="b.id"><td>{{ b.trek_name }}</td><td>{{ b.location }}</td><td>{{ b.startDate }} → {{ b.endDate }}</td></tr></tbody>
      </table>
      <h6>Cancelled</h6>
      <table class="table table-sm bg-white shadow-sm">
        <tbody><tr v-for="b in cancelled" :key="b.id"><td>{{ b.trek_name }}</td><td>{{ b.location }}</td></tr></tbody>
      </table>
    </div>`,
};

const userProfile = {
  data() { return { form: { fullName: "", phone: "", password: "" }, msg: "" }; },
  created() {
    const u = trek_manager.getUser();
    this.form.fullName = u.fullName; this.form.phone = u.phone || "";
  },
  methods: {
    async save() {
      const d = await trek_manager.put("/auth/profile", this.form);
      trek_manager.setSession(trek_manager.getToken(), d.user);
      this.msg = "Profile updated."; this.form.password = "";
    },
  },
  template: `
    <div class="container" style="max-width:480px;">
      <h2 class="mb-3">My Profile</h2>
      <div class="alert alert-success py-2" v-if="msg">{{ msg }}</div>
      <form @submit.prevent="save" class="card p-3 shadow-sm">
        <div class="mb-2"><label class="form-label">Full Name</label><input v-model="form.fullName" class="form-control"></div>
        <div class="mb-2"><label class="form-label">Phone</label><input v-model="form.phone" class="form-control"></div>
        <div class="mb-2"><label class="form-label">New Password (optional)</label><input type="password" v-model="form.password" class="form-control"></div>
        <button class="btn btn-success">Save</button>
      </form>
    </div>`,
};

const userExports = {
  data() { return { jobs: [] }; },
  async created() { await this.refresh(); },
  methods: {
    async refresh() { const d = await trek_manager.get("/user/exports"); this.jobs = d.jobs; },
    async trigger() { await trek_manager.post("/user/exports"); await this.refresh(); },
    async download(j) { await trek_manager.downloadFile(`/user/exports/${j.id}/download`, "booking_history.csv"); },
  },
  template: `
    <div class="container">
      <h2 class="mb-3">Export Booking History</h2>
      <button class="btn btn-success me-2 mb-3" @click="trigger">Export as CSV</button>
      <button class="btn btn-outline-secondary mb-3" @click="refresh">Refresh Status</button>
      <table class="table bg-white shadow-sm">
        <thead><tr><th>Job</th><th>Status</th><th>Requested</th><th></th></tr></thead>
        <tbody>
          <tr v-for="j in jobs" :key="j.id">
            <td>#{{ j.id }}</td>
            <td><span class="badge" :class="j.status==='Done'?'bg-success':(j.status==='Failed'?'bg-danger':'bg-warning text-dark')">{{ j.status }}</span></td>
            <td>{{ new Date(j.createdAt).toLocaleString() }}</td>
            <td><button v-if="j.status==='Done'" class="btn btn-sm btn-outline-success" @click="download(j)">Download</button></td>
          </tr>
        </tbody>
      </table>
      <p class="text-muted small">This runs as a background Celery job - click "Refresh Status" to check when it's ready.</p>
    </div>`,
};
