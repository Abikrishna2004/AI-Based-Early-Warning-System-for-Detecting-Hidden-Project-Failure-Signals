// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics, isSupported } from "firebase/analytics";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAgBcyrFFaNLYE6O_MEuk0I9_tjLTLRQZY",
  authDomain: "compilepulse.firebaseapp.com",
  projectId: "compilepulse",
  storageBucket: "compilepulse.firebasestorage.app",
  messagingSenderId: "384019181044",
  appId: "1:384019181044:web:c1a1bcf2b2c9794fa0dda1",
  measurementId: "G-K8QH5861JD"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Analytics conditionally (safeguarded for browser environments)
let analytics = null;
if (typeof window !== "undefined") {
  isSupported().then((supported) => {
    if (supported) {
      analytics = getAnalytics(app);
    }
  }).catch(() => {
    // Analytics fallback if disabled or unsupported
  });
}

export { app, analytics };
