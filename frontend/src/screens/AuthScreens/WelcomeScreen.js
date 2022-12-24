import { SafeAreaView, StyleSheet, Text, TouchableOpacity, View,NativeModules, Platform } from "react-native";
import MaterialCommunityIcons from "react-native-vector-icons/MaterialCommunityIcons";
import AntDesign from 'react-native-vector-icons/AntDesign'
import React from "react";
const {StatusBarManager} = NativeModules

import { COLORS, CONSTANTS } from "../../utils/constants";

const WelcomeScreen = ({ navigation, route }) => {
  return (
    <SafeAreaView style={{...styles.container,paddingTop:Platform.OS==='android'?StatusBarManager.HEIGHT:0}}>
    <View style={styles.container}>
      <Text style={styles.title}>Trix Wallet</Text>
      <View style={{flex:1,justifyContent:'center',alignItems:'center'}}>
        <MaterialCommunityIcons name="home" size={100} />
      </View>
      <TouchableOpacity onPress={() => navigation.navigate("Login")}>
        <View style={styles.btn}>
          <Text style={{color:'#fff',fontSize:18,fontWeight:'800'}}>Get Started</Text>
          <AntDesign name="right" color={"white"} size={32} />
        </View>
      </TouchableOpacity>
    </View>
    </SafeAreaView>
  );
};

export default WelcomeScreen;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding:8,
    width: "100%",
    height: "100%",
  },
  title: {
    fontSize: 30,
    fontWeight: "800",
    fontStyle: "normal",
    textAlign:'center',
    paddingTop:20
  },
  btn: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: COLORS.green,
    color: COLORS.white,
    margin:4,
    flexDirection:'row',
    borderRadius:8,
    padding:8
  },
});
