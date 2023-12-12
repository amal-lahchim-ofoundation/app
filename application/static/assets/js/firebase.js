<script type="module">
    // Import the functions you need from the SDKs you need
    import { initializeApp } from "https://www.gstatic.com/firebasejs/10.3.0/firebase-app.js";
    import { getAnalytics } from "https://www.gstatic.com/firebasejs/10.3.0/firebase-analytics.js";
    // TODO: Add SDKs for Firebase products that you want to use
    // https://firebase.google.com/docs/web/setup#available-libraries
  
    // Your web app's Firebase configuration
    // For Firebase JS SDK v7.20.0 and later, measurementId is optional
    const firebaseConfig = {
      apiKey: "AIzaSyCeAAdqRAvYpFhiJ6eQpihtt4s57adefJs",
      authDomain: "chat-psychologist-ai.firebaseapp.com",
      databaseURL: "https://chat-psychologist-ai-default-rtdb.europe-west1.firebasedatabase.app",
      projectId: "chat-psychologist-ai",
      storageBucket: "chat-psychologist-ai.appspot.com",
      messagingSenderId: "455661561573",
      appId: "1:455661561573:web:ce1af3be0ceeec8109560c",
      measurementId: "G-XCBTC9YDLW"
    };
  
    // Initialize Firebase
    const app = initializeApp(firebaseConfig);
    const analytics = getAnalytics(app);
  </script>