import React, { useState } from "react";
import { View, Button, Image, Text, Alert } from "react-native";
import { launchCamera } from "react-native-image-picker";

const UploadServiceTag = () => {
    const [imageUri, setImageUri] = useState(null);
    const [serviceTag, setServiceTag] = useState(null);

    const openCamera = () => {
        launchCamera({ mediaType: "photo", cameraType: "back" }, (response) => {
            if (response.didCancel) {
                Alert.alert("Cancelled", "User cancelled camera.");
            } else if (response.errorMessage) {
                Alert.alert("Error", response.errorMessage);
            } else if (response.assets && response.assets.length > 0) {
                const uri = response.assets[0].uri;
                setImageUri(uri);
                uploadImage(uri);
            } else {
                Alert.alert("Error", "No image captured.");
            }
        });
    };

    const uploadImage = async (uri) => {
        const formData = new FormData();
        formData.append("image", {
            uri,
            name: "service_tag.jpg",
            type: "image/jpeg",
        });

        try {
            let response = await fetch("https://service-tag-detection-4.onrender.com/upload", {
                method: "POST",
                body: formData,
                headers: { "Content-Type": "multipart/form-data" },
            });

            let result = await response.json();
            if (response.ok && result.service_tag) {
                setServiceTag(result.service_tag);
            } else {
                setServiceTag("Service Tag not detected");
            }
        } catch (error) {
            Alert.alert("Upload Error", `Failed to upload image: ${error.message}`);
        }
    };

    return (
        <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
            <Button title="Capture Service Tag" onPress={openCamera} />
            {imageUri && <Image source={{ uri: imageUri }} style={{ width: 200, height: 200, marginTop: 10 }} />}
            {serviceTag && <Text style={{ marginTop: 10, fontSize: 16 }}>Detected: {serviceTag}</Text>}
        </View>
    );
};

export default UploadServiceTag;
