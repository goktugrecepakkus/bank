import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.rykard.bank',
  appName: 'Rykard Bank',
  webDir: 'public',
  server: {
    androidScheme: 'https'
  }
};

export default config;
