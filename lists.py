
#  Special treatment for some claims

#  LBRY Inc channels
inc = set(["f3da2196b5151570d980b34d311ee0973225a68e",
           "70b8a88fc6e5ce9e4d6e8721536688484ecd79f4",
           "3fda836a92faaceedfe398225fb9b2ee2ed1f01a",
           "e48d2b50501159034f68d53321f67b8aa5b1d771",
           "e8fed337dc4ee260f4bcfa6d24ae1e4dd75c2fb3",
           "4c29f8b013adea4d5cca1861fb2161d5089613ea",
           "19e7d3104e12fe3eeaef05933af033242eeb42c3"])

# LBRY Foundation Channels
lbryf = set(["f8d6eccd887c9cebd36b1d42aa349279b7f5c3ed",
          "e11e2fc3056137948d2cc83fb5ca2ce9b57025ec",
          "735d7177812f4a6b9acb2204c7a7fee7d9faeb9b",
          "1ba5acff747615510cf3f6089f54d5de669ad94f",
          "f3b9973e1725ecb50da3e6fa4d47343c98ef0382",
          "4506db7fb52d3ec5d3a024c870bf86fc35f7b6a3",
          "0f3a709eac3c531a68c97c7a48b2e37a532edb03",
          "36b7bd81c1f975878da8cfe2960ed819a1c85bb5",
          "e5f33f22ef656cb1595140409850a04d60aa474b",
          "631ca9fce459f1116ae5317486c7f4af69554742",
          "4caa1f92fb477caed1ce07cb7762a2249050a59c",
          "56e86eb938c0b93beccde0fbaaead65755139a10",
          "60ea26a907f25bcbbc8215007eef2bf0fb846f5c",
          "d0174cf90b6ec4e26ee2fc013714b0803dec5dd1",
          "3849a35ae6122e0b7a035c2ba66e97b9e4ab9efa",
          "aaeda15cc0cafe689793a00d5e6c5a231e3b6ee8",
          "2bfe6cdb24a21bdc1b76fb7c416edd50e9e85945",
          "3b807b82be6fadc0db4a057955766cea230839b9"])

lbrynomics = set(["2d09719c8e06ab54ca5c1b4e44ddf3ee9d30241f",
                  "36b7bd81c1f975878da8cfe2960ed819a1c85bb5",
                  "e5f33f22ef656cb1595140409850a04d60aa474b"])

# Channels to be promoted
# promo = set()
# promo = set([""])

# Given mature tag by us
manual_mature = set(["f24ab6f03d96aada87d4e14b2dac4aa1cee8d787",
                 "fd4b56c7216c2f96db4b751af68aa2789c327d48",
                 "ebe983567c5b64970d5dff2fe78dd1573f0d7b61"])

# Grey list (quietly disable link)
grey_list = set(["ca8cfeb5b6660a0b8874593058178b7ce6af5fed",
              "6c1119f18fd7a15fc7535fcb9eec3aa22af66b6b",
              "3097b755d3b8731e6103cc8752cb1b6c79da3b85",
              "11c2f6bb38f69a25dea3d0fbef67e2e3a83a1263",
              "7acf8b2fcd212afa2877afe289309a20642880c4",
              "b01a44af8b71c0c2001a78303f319ca960d341cf",
              "bc89d67d9f4d0124c347fd2c4a04e1696e8ba8b1",
              "14fcd92ad24c1f1bc50f6cbc1e972df79387d05c",
              "977cd1c90eefe4c9831f5c93b2359202733a9c2e",
              "b3c6591b2f64c843fa66edda91ceab91d452f94f",
              "67c1ce0d5754490cfa573ca27f8473ba793d1842",
              "1713b1a9d2fd4e68bf3ff179cba246d527f67d56",
              "37e533eca2d0477f7123532144568fa3f7fe7ad7"])

# DMCA'd channels + rewards scammers (do not appear)
# Also those who appear to be faking their following, or other things
black_list = set([ "98c39de1c681139e43131e4b32c2a21272eef06e",
                "321b33d22c8e24ef207e3f357a4573f6a56611f3",
                "9ced2a722e91f28e9d3aea9423d34e08fb11e3f4",
                "d5557f4c61d6725f1a51141bbee43cdd2576e415",
                "35100b76e32aeb2764d334186249fa1b90d6cd74",
                "f2fe17fb1c62c22f8319c38d0018726928454112",
                "17db8343914760ba509ed1f8c8e34dcc588614b7",
                "06a31b83cd38723527861a1ca5349b0187f92193",
                "9b7a749276c69f39a2d2d76ca4353c0d8f75217d",
                "b1fa196661570de64ff92d031116a2985af6034c",
                "4e5e34d0ab3cae6f379dad75afadb0c1f683d30f",
                "86612188eea0bda3efc6d550a7ad9c96079facff",
                "00aa9655c127cccb2602d069e1982e08e9f96636",
                "4f2dba9827ae28a974fbc78f1b12e67b8e0a32c9",
                "c133c44e9c6ee71177f571646d5b0000489e419f",
                "eeb3c6452b240a9f6a17c06887547be54a90a4b9",
                "f625ef83a3f34cac61b6b3bdef42be664fd827da",
                "ed77d38da413377b8b3ee752675662369b7e0a49",
                "481c95bd9865dc17770c277ae50f0cc306dfa8af",
                "3c5aa133095f97bb44f13de7c85a2a4dd5b4fcbe",
                "bd6abead1787fa94722bd7d064f847de76de5655",
                "6114b2ce20b55c40506d4bd3f7d8f917b1c37a75",
                "0c65674e28f2be555570c5a3be0c3ce2eda359d1",
                "3395d03f379888ffa789f1fa45d6619c2037e3de",
                "cd31c9ddea4ac4574df50a1f84ee86aa17910ea2",
                "9d48c8ab0ad53c392d4d6052daf5f8a8e6b5a185",
                "51fbdb73893c1b04a7d4c4465ffcd1138abc9e93",
                "5183307ce562dad27367bdf94cdafde38756dca7",
                "56dca125e775b2fe607d3d8d6c29e7ecfa3cbd96",
                "a58926cb716c954bdab0187b455a63a2c592310e",
                "aa83130864bf22c66934c1af36182c91219233aa",
                "f3c1fda9bf1f54710b62ffe4b14be6990288d9ff",
                "6291b3b53dde4160ce89067281300585bdf51905",
                "eeef31480a14684a95898ecd3bcf3a5569e41a28",
                "9530d1af1b9f9982149ecf5785f74695b96a1c32",
                "8b8b3c8cd3e8364c37067b80bd5a20c09a0a0094",
                "725189cd101ff372edbce1c05ef04346864d3254",
                "35100b76e32aeb2764d334186249fa1b90d6cd74",
                "47beabb163e02e10f99838ffc10ebc57f3f13938",
                "e0bb55d4d6aec9886858df8f1289974e673309c7",
                "242734793097302d33b6a316c9db8d17b4beb18e",
                "71d3256c267ccc875df366258b9eff4766d6cb57",
                "dee09cad16900936d6af97154a6510a09587ad42",
                "357ce885e22f2a7bd426ac36224722d64fc90ce6",
                "c3ab2407e295cd267ced06d1fad2ed09b8d5643e",
                "37b96ce8ae7a5564174111573105ee7efe4cd2fc",
                "2849e111e747ce5883d2409046fefa03029daaec",
                "29531246ce976d00a41741555edae4028c668205",
                "477b11086e2d5065d2dcbc0d9389ab31f75a5f5a",
                "82360163ab15de0fbe9c87c1f9b630e66c5c332b",
                "0d4078fe826733fc19808115dec71c530b482c95" ])

# Legit channels that are exempt from the quality filter criteria
# (mostly these are people who sell their LBC)
white_list = set(["b174a8f5ff9e7197b739b72a57cd58a6d40a4279",
                  "24d6fddfc6098e12b3197273e8161f63e62f47f0",
                  "06b6d6d6a893fb589ec2ded948f5122856921ed5",
                  "828174a6adcdeee74de5211db1d006716aa54d07",
                  "1ba5acff747615510cf3f6089f54d5de669ad94f",
                  "e5f33f22ef656cb1595140409850a04d60aa474b"])

