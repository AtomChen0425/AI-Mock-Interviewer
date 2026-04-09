import { createApp } from 'vue';
import App from './App.vue';
import './index.css';

import vue3GoogleLogin from 'vue3-google-login';

const app = createApp(App);

app.use(vue3GoogleLogin, {
  clientId: '1089487447874-9dntifnrmkij7kob1k28bk2edsm1uqmh.apps.googleusercontent.com'
});

app.mount('#root');
