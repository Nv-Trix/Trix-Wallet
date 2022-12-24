import { StyleSheet, Text, View ,ActivityIndicator} from 'react-native'
import React,{useState,useEffect} from 'react'

import AsyncStorage from '@react-native-async-storage/async-storage'

const SplashScreem = () => {
    const [animating, setAnimating] = useState(true);
    useEffect(() => {
    setTimeout(() => {
      setAnimating(false);
      //Check if user_id is set or not
      //If not then send for Authentication
      //else send to Home Screen
      AsyncStorage.getItem('token').then((value) =>
        navigation.replace(
          value === null ? 'Auth' : 'DrawerNavigationRoutes'
        ),
      );
    }, 5000);
  }, []);
    return (
    <View style={styles.container}>
      <Image
        source={require('../images/logo.png')}
        style={{width: '90%', resizeMode: 'contain', margin: 30}}
      />
      <ActivityIndicator
        animating={animating}
        color="#FFFFFF"
        size="large"
        style={styles.activityIndicator}
      />
    </View>
  )
}

export default SplashScreem

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#307ecc',
  },
  activityIndicator: {
    alignItems: 'center',
    height: 80,
  },
})