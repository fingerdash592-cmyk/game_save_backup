#include <iostream>
#include <fstream>
#include <filesystem>
#include <vector>
#include <string>
#include <cstring>
#include <zip.h>

#define MD5_IMPLEMENTATION
#include "md5.h"

using namespace std;
using namespace std::filesystem;

struct PackagedFile {
    char md5[33];
    uint8_t* zip_data;
    size_t zip_size;
};

string get_file_md5(const path& filepath) {
    std::ifstream file(filepath, std::ios::binary);
    if (!file.is_open()) return "";

    MD5 md5;
    char buffer[8192];

    while (file.read(buffer, sizeof(buffer))) {
        md5.update(reinterpret_cast<uint8_t*>(buffer), file.gcount());
    }
    if (file.gcount() > 0) {
        md5.update(reinterpret_cast<uint8_t*>(buffer), file.gcount());
    }
    md5.finalize();
    return md5.toString();
}

extern "C" {

#ifdef _WIN32
__declspec(dllexport)
#endif
PackagedFile* pack_file_to_memory(const char* file_path) {
    path p(file_path);

    if (!exists(p) || !is_regular_file(p)) {
        return nullptr;
    }

    string md5_str = get_file_md5(p);
    string orig_name = p.filename().string();

    struct zip_t* zip = zip_stream_open(nullptr, 0, 6, 'w');
    if (!zip) return nullptr;

    zip_entry_open(zip, orig_name.c_str());
    zip_entry_fwrite(zip, p.u8string().c_str());
    zip_entry_close(zip);

    void* out_buf = nullptr;
    size_t out_size = 0;

    zip_stream_copy(zip, &out_buf, &out_size);
    zip_stream_close(zip);

    PackagedFile* res = new PackagedFile();

    strncpy(res->md5, md5_str.c_str(), 32);
    res->md5[32] = '\0';

    res->zip_size = out_size;
    res->zip_data = static_cast<uint8_t*>(out_buf);

    return res;
}

#ifdef _WIN32
__declspec(dllexport)
#endif
void free_packaged_file(PackagedFile* res) {
    if (res) {
        if (res->zip_data) {
            free(res->zip_data);
        }
        delete res;
    }
}
}