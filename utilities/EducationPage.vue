<template>
  <div class="profile-page-container">
    <div class="header">
      <span class="icon">🎓</span>
      <div class="title small-text">Edukacja</div>
    </div>
    <div>
      <img :src="apiUrl + educationData.photoUrl.replace(/\\/g, '/')" alt="Education Photo" class="photo-frame"/>
    </div>
    <h2 class="big-text">{{ educationData.startYear }} - {{ educationData.endYear }}</h2>
    <p class="small-text">{{ educationData.description }}</p>
    <div class="location-arrow">
      <span class="icon">👇</span>
    </div>
    <div class="location-name small-text">{{ educationData.place }}</div>
  </div>
</template>

<script>
export default {
  name: 'EducationPage',
  props: {
    educationData: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      apiUrl: process.env.VUE_APP_API_URL
    };
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/scss/MemorialProfile.scss';

.profile-page-container {
  background-image: url('@/assets/images/profile_education_background.png');
  padding-top: 8px; /* Reduced padding to decrease space at the top */
}

.header .icon {
  font-size: 24px;
}

.title {
  margin-top: 8px;
  // Inherits small-text styles from profile.scss
}

.photo-frame {
  margin-top: 16px;
  border: 1px solid #000;
  height: 16rem; /* Further reduced height */
  display: flex;
  justify-content: center;
  align-items: center;
}


.location-arrow .icon {
  font-size: 24px; // Adjust size as needed
  display: block; // Ensure the icon is centered
  margin: 16px auto; // Center the icon horizontally and add some margin
}

.location-name {
  margin-top: 8px;
  // Inherits small-text styles from profile.scss
}

/* Additional styles can be added as needed to match the design */
</style>
