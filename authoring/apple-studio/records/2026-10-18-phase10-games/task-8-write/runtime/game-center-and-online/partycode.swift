// Prints GameKit's party-code alphabet and validates sample codes.
// No Game Center sign-in is needed: both members are class-level.
import GameKit

let alphabet = GKGameActivity.validPartyCodeAlphabet
print("alphabet count:", alphabet.count)
print("alphabet:", alphabet.joined())
for code in ["2MP4-9CMF", "2345-CFGH", "1234-5678", "AB-CD", "ABCDEFG-HIJKLMN",
             "abcd-efgh", "ABCD-EFG", "O0I1-ABCD", "ABCDEF-GHJKLM",
             "cfgh-jmpq", "CF-GH", "CFGHJM-PQRVWX", "CFGHJMP-QRVWXCF", "CFGH-JMP",
             "12-34", "0123-4567", "CFGHJMPQ"] {
    print(code, GKGameActivity.isValidPartyCode(code))
}
