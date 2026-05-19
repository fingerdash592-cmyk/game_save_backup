cmake_minimum_required(VERSION 3.10)
project(game_save_backup)

set(CMAKE_CXX_STANDARD 17)

add_executable(archivator archivator.cpp
        include/zip.c
        include/miniz.h
        include/md5.h)

target_include_directories(archivator PRIVATE include)

