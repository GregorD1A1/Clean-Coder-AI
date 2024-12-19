<template>
  <Notification v-show="notificationMessage" :message="notificationMessage" :type="notificationType" />
  <h1>Edit Profile</h1>
  <form @submit.prevent="handleProfileUpdate">
    <div>
      <label for="fullName">Full Name:</label>
      <input type="text" v-model="fullName" required />
    </div>
    <div>
      <label for="cookingExperience">Cooking Experience:</label>
      <select v-model="cookingExperience" required>
        <option value="beginner">Beginner</option>
        <option value="intermediate">Intermediate</option>
        <option value="advanced">Advanced</option>
        <option value="professional">Professional Chef</option>
      </select>
    </div>
    <div>
      <label for="startDate">Available From:</label>
      <input type="date" v-model="startDate" :min="today" required />
    </div>
    <div>
      <label for="endDate">Available Until:</label>
      <input type="date" v-model="endDate" :min="today" :disabled="noEndDate" required />
      <div class="checkbox-container">
        <input type="checkbox" id="noEndDate" v-model="noEndDate" />
        <label for="noEndDate"> No End Date</label>
      </div>
    </div>
    <button type="submit">Update Profile</button>
  </form>
</template>

<script>
import Notification from '@/components/Notification.vue';
import { useAuthStore } from '@/stores/auth';

export default {
  components: {
    Notification,
  },
  data() {
    return {
      fullName: '',
      cookingExperience: '',
      startDate: '',
      endDate: '',
      noEndDate: false,
      apiUrl: import.meta.env.VITE_API_URL,
      notificationMessage: '',
      notificationType: 'positive',
    };
  },
  computed: {
    today() {
      return new Date().toISOString().split('T')[0];
    },
  },
  created() {
    const authStore = useAuthStore();
    if (!authStore.isLoggedIn) {
      this.$router.push('/login');
    } else {
      this.loadProfile();
    }
  },
  methods: {
    async loadProfile() {
      try {
        const response = await fetch(`${this.apiUrl}/profile-data`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        if (!response.ok) {
          throw new Error('Failed to load profile');
        }
        const data = await response.json();
        this.fullName = data.full_name || '';
        this.cookingExperience = data.cooking_experience || '';
        this.startDate = data.start_date || '';
        this.endDate = data.end_date || '';
        this.noEndDate = data.end_date === null;
      } catch (error) {
        this.showNotification(error.message, 'negative');
      }
    },
    async handleProfileUpdate() {
      const payload = {
        fullName: this.fullName,
        cookingExperience: this.cookingExperience,
        startDate: this.startDate,
        endDate: this.noEndDate ? null : this.endDate,
      };
      try {
        const response = await fetch(`${this.apiUrl}/profile-edit`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(payload),
        });
        if (!response.ok) {
          throw new Error('Profile update failed');
        }
        this.showNotification('Profile updated successfully', 'positive');
        setTimeout(() => {
          this.$router.push('/');
        }, 2500);
      } catch (error) {
        this.showNotification(error.message, 'negative');
      }
    },
    showNotification(message, type) {
      this.notificationMessage = message;
      this.notificationType = type;
      setTimeout(() => {
        this.notificationMessage = '';
      }, 2000);
    },
  },
};
</script>

<style scoped src="@/assets/styles/profileEditStyles.css"></style>
