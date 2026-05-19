/* MD5.H - header file for MD5C.C */
#ifndef MD5_H
#define MD5_H

#include <string>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <cstdint>

class MD5 {
public:
    MD5();
    void init();
    void update(const uint8_t *input, size_t length);
    void update(const std::string &input);
    void finalize();
    std::string toString() const;

private:
    void transform(const uint8_t block[64]);
    void encode(const uint32_t *input, uint8_t *output, size_t length);
    void decode(const uint8_t *input, uint32_t *output, size_t length);

    static void memcpy_generic(void *s1, const void *s2, size_t n);
    static void memset_generic(void *s, int c, size_t n);

    uint32_t state[4];                                   /* state (ABCD) */
    uint64_t count;        /* number of bits, modulo 2^64 (lsb first) */
    uint8_t buffer[64];                         /* input buffer */
    uint8_t digest[16];                             /* message digest */
    bool finalized;

    static constexpr uint32_t S11 = 7;
    static constexpr uint32_t S12 = 12;
    static constexpr uint32_t S13 = 17;
    static constexpr uint32_t S14 = 22;
    static constexpr uint32_t S21 = 5;
    static constexpr uint32_t S22 = 9;
    static constexpr uint32_t S23 = 14;
    static constexpr uint32_t S24 = 20;
    static constexpr uint32_t S31 = 4;
    static constexpr uint32_t S32 = 11;
    static constexpr uint32_t S33 = 16;
    static constexpr uint32_t S34 = 23;
    static constexpr uint32_t S41 = 6;
    static constexpr uint32_t S42 = 10;
    static constexpr uint32_t S43 = 15;
    static constexpr uint32_t S44 = 21;

    static uint32_t F(uint32_t x, uint32_t y, uint32_t z);
    static uint32_t G(uint32_t x, uint32_t y, uint32_t z);
    static uint32_t H(uint32_t x, uint32_t y, uint32_t z);
    static uint32_t I(uint32_t x, uint32_t y, uint32_t z);
    static uint32_t rotate_left(uint32_t x, int n);
    static void FF(uint32_t &a, uint32_t b, uint32_t c, uint32_t d, uint32_t x, uint32_t s, uint32_t ac);
    static void GG(uint32_t &a, uint32_t b, uint32_t c, uint32_t d, uint32_t x, uint32_t s, uint32_t ac);
    static void HH(uint32_t &a, uint32_t b, uint32_t c, uint32_t d, uint32_t x, uint32_t s, uint32_t ac);
    static void II(uint32_t &a, uint32_t b, uint32_t c, uint32_t d, uint32_t x, uint32_t s, uint32_t ac);
};

#endif /* MD5_H */

/* MD5.CC - implementation of MD5 message-digest algorithm */
#ifdef MD5_IMPLEMENTATION

#include <cstring>

MD5::MD5() {
    init();
}

void MD5::init() {
    finalized=false;
    count = 0;
    state[0] = 0x67452301;
    state[1] = 0xefcdab89;
    state[2] = 0x98badcfe;
    state[3] = 0x10325476;
}

uint32_t MD5::F(uint32_t x, uint32_t y, uint32_t z) { return (x & y) | (~x & z); }
uint32_t MD5::G(uint32_t x, uint32_t y, uint32_t z) { return (x & z) | (y & ~z); }
uint32_t MD5::H(uint32_t x, uint32_t y, uint32_t z) { return x ^ y ^ z; }
uint32_t MD5::I(uint32_t x, uint32_t y, uint32_t z) { return y ^ (x | ~z); }
uint32_t MD5::rotate_left(uint32_t x, int n) { return (x << n) | (x >> (32-n)); }

void MD5::FF(uint32_t &a, uint32_t b, uint32_t c, uint32_t d, uint32_t x, uint32_t s, uint32_t ac) {
    a = rotate_left(a + F(b,c,d) + x + ac, s) + b;
}
void MD5::GG(uint32_t &a, uint32_t b, uint32_t c, uint32_t d, uint32_t x, uint32_t s, uint32_t ac) {
    a = rotate_left(a + G(b,c,d) + x + ac, s) + b;
}
void MD5::HH(uint32_t &a, uint32_t b, uint32_t c, uint32_t d, uint32_t x, uint32_t s, uint32_t ac) {
    a = rotate_left(a + H(b,c,d) + x + ac, s) + b;
}
void MD5::II(uint32_t &a, uint32_t b, uint32_t c, uint32_t d, uint32_t x, uint32_t s, uint32_t ac) {
    a = rotate_left(a + I(b,c,d) + x + ac, s) + b;
}

void MD5::transform(const uint8_t block[64]) {
    uint32_t a = state[0], b = state[1], c = state[2], d = state[3], x[16];
    decode(block, x, 64);

    FF(a, b, c, d, x[ 0], S11, 0xd76aa478); FF(d, a, b, c, x[ 1], S12, 0xe8c7b756);
    FF(c, d, a, b, x[ 2], S13, 0x242070db); FF(b, c, d, a, x[ 3], S14, 0xc1bdceee);
    FF(a, b, c, d, x[ 4], S11, 0xf57c0faf); FF(d, a, b, c, x[ 5], S12, 0x4787c62a);
    FF(c, d, a, b, x[ 6], S13, 0xa8304613); FF(b, c, d, a, x[ 7], S14, 0xfd469501);
    FF(a, b, c, d, x[ 8], S11, 0x698098d8); FF(d, a, b, c, x[ 9], S12, 0x8b44f7af);
    FF(c, d, a, b, x[10], S13, 0xffff5bb1); FF(b, c, d, a, x[11], S14, 0x895cd7be);
    FF(a, b, c, d, x[12], S11, 0x6b901122); FF(d, a, b, c, x[13], S12, 0xfd987193);
    FF(c, d, a, b, x[14], S13, 0xa679438e); FF(b, c, d, a, x[15], S14, 0x49b40821);

    GG(a, b, c, d, x[ 1], S21, 0xf61e2562); GG(d, a, b, c, x[ 6], S22, 0xc040b340);
    GG(c, d, a, b, x[11], S23, 0x265e5a51); GG(b, c, d, a, x[ 0], S24, 0xe9b6c7aa);
    GG(a, b, c, d, x[ 5], S21, 0xd62f105d); GG(d, a, b, c, x[10], S22,  0x2441453);
    GG(c, d, a, b, x[15], S23, 0xd8a1e681); GG(b, c, d, a, x[ 4], S24, 0xe7d3fbc8);
    GG(a, b, c, d, x[ 9], S21, 0x21e1cde6); GG(d, a, b, c, x[14], S22, 0xc33707d6);
    GG(c, d, a, b, x[ 3], S23, 0xf4d50d87); GG(b, c, d, a, x[ 8], S24, 0x455a14ed);
    GG(a, b, c, d, x[13], S21, 0xa9e3e905); GG(d, a, b, c, x[ 2], S22, 0xfcefa3f8);
    GG(c, d, a, b, x[ 7], S23, 0x676f02d9); GG(b, c, d, a, x[12], S24, 0x8d2a4c8a);

    HH(a, b, c, d, x[ 5], S31, 0xfffa3942); HH(d, a, b, c, x[ 8], S32, 0x8771f681);
    HH(c, d, a, b, x[11], S33, 0x6d9d6122); HH(b, c, d, a, x[14], S34, 0xfde5380c);
    HH(a, b, c, d, x[ 1], S31, 0xa4beea44); HH(d, a, b, c, x[ 4], S32, 0x4bdecfa9);
    HH(c, d, a, b, x[ 7], S33, 0xf6bb4b60); HH(b, c, d, a, x[10], S34, 0xbebfbc70);
    HH(a, b, c, d, x[13], S31, 0x289b7ec6); HH(d, a, b, c, x[ 0], S32, 0xeaa127fa);
    HH(c, d, a, b, x[ 3], S33, 0xd4ef3085); HH(b, c, d, a, x[ 6], S34,  0x4881d05);
    HH(a, b, c, d, x[ 9], S31, 0xd9d4d039); HH(d, a, b, c, x[12], S32, 0xe6db99e5);
    HH(c, d, a, b, x[15], S33, 0x1fa27cf8); HH(b, c, d, a, x[ 2], S34, 0xc4ac5665);

    II(a, b, c, d, x[ 0], S41, 0xf4292244); II(d, a, b, c, x[ 7], S42, 0x432aff97);
    II(c, d, a, b, x[14], S43, 0xab9423a7); II(b, c, d, a, x[ 5], S44, 0xfc93a039);
    II(a, b, c, d, x[12], S41, 0x655b59c3); II(d, a, b, c, x[ 3], S42, 0x8f0ccc92);
    II(c, d, a, b, x[10], S43, 0xffeff47d); II(b, c, d, a, x[ 1], S44, 0x85845dd1);
    II(a, b, c, d, x[ 8], S41, 0x6fa87e4f); II(d, a, b, c, x[15], S42, 0xfe2ce6e0);
    II(c, d, a, b, x[ 6], S43, 0xa3014314); II(b, c, d, a, x[13], S44, 0x4e0811a1);
    II(a, b, c, d, x[ 4], S41, 0xf7537e82); II(d, a, b, c, x[11], S42, 0xbd3af235);
    II(c, d, a, b, x[ 2], S43, 0x2ad7d2bb); II(b, c, d, a, x[ 9], S44, 0xeb86d391);

    state[0] += a; state[1] += b; state[2] += c; state[3] += d;
}

void MD5::encode(const uint32_t *input, uint8_t *output, size_t length) {
    for(size_t i=0, j=0; j<length; i++, j+=4) {
        output[j]=(uint8_t)(input[i] & 0xff);
        output[j+1]=(uint8_t)((input[i] >> 8) & 0xff);
        output[j+2]=(uint8_t)((input[i] >> 16) & 0xff);
        output[j+3]=(uint8_t)((input[i] >> 24) & 0xff);
    }
}

void MD5::decode(const uint8_t *input, uint32_t *output, size_t length) {
    for(size_t i=0, j=0; j<length; i++, j+=4) {
        output[i]=((uint32_t)input[j]) | (((uint32_t)input[j+1]) << 8) |
                  (((uint32_t)input[j+2]) << 16) | (((uint32_t)input[j+3]) << 24);
    }
}

void MD5::update(const uint8_t *input, size_t length) {
    size_t index = count / 8 % 64;
    count += (length << 3);
    size_t partLen = 64 - index;
    size_t i = 0;

    if(length >= partLen) {
        memcpy_generic(&buffer[index], input, partLen);
        transform(buffer);
        for (i = partLen; i + 63 < length; i += 64) transform(&input[i]);
        index = 0;
    }
    memcpy_generic(&buffer[index], &input[i], length-i);
}

void MD5::update(const std::string &input) {
    update(reinterpret_cast<const uint8_t*>(input.c_str()), input.length());
}

void MD5::finalize() {
    if(finalized) return;
    uint8_t padding[64] = { 0x80 };
    uint8_t bits[8];
    encode((uint32_t*)&count, bits, 8);

    size_t index = count / 8 % 64;
    size_t padLen = (index < 56) ? (56 - index) : (120 - index);
    update(padding, padLen);
    update(bits, 8);

    encode(state, digest, 16);
    finalized = true;
}

std::string MD5::toString() const {
    if(!finalized) return "";
    std::ostringstream oss;
    for(int i=0; i<16; ++i) {
        oss << std::hex << std::setw(2) << std::setfill('0') << (int)digest[i];
    }
    return oss.str();
}

void MD5::memcpy_generic(void *s1, const void *s2, size_t n) {
    std::memcpy(s1, s2, n);
}
void MD5::memset_generic(void *s, int c, size_t n) {
    std::memset(s, c, n);
}


#endif // MD5_IMPLEMENTATION