# Copyright (c) 2014-2020, The Monero Project
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are
# permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of
#    conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list
#    of conditions and the following disclaimer in the documentation and/or other
#    materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be
#    used to endorse or promote products derived from this software without specific
#    prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# - Try to find readline include dirs and libraries 
#
# Automatically finds the fast Gold Linker, if it's found in PATH.
#
# Usage of this module as follows:
#
#     project(monero)
#     include(FindGoldLinker)
#
# Properties modified by this module:
#
#    CMAKE_EXE_LINKER_FLAGS    - for executables
#    CMAKE_STATIC_LINKER_FLAGS - for STATIC libraries
#    CMAKE_SHARED_LINKER_FLAGS - for SHARED libraries
#    CMAKE_MODULE_LINKER_FLAGS - for MODULEs.

find_program(GOLD_LINKER_FOUND ld.gold)
if (GOLD_LINKER_FOUND)
	# Try to link a test program with Gold Linker, in order to verify if it really works.
	set(TEST_PROJECT "${CMAKE_BINARY_DIR}/${CMAKE_FILES_DIRECTORY}/CMakeTmp")
	file(WRITE "${TEST_PROJECT}/CMakeLists.txt" [=[
cmake_minimum_required(VERSION 3.1)
project(test)
option (GOLD "")
file(WRITE "${CMAKE_SOURCE_DIR}/test.cpp" "int main() { return 0; }")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fuse-ld=${GOLD}")
add_executable(test test.cpp)
]=])
	try_compile(RET "${TEST_PROJECT}/build" "${TEST_PROJECT}" "test" CMAKE_FLAGS -DGOLD="${GOLD_LINKER_FOUND}")
	unset(TEST_PROJECT)
	if (${RET})
		# Success
		message(STATUS "Found usable Gold Linker: ${GOLD_LINKER_FOUND}")
		set(CMAKE_EXE_LINKER_FLAGS    "${CMAKE_EXE_LINKER_FLAGS}    -fuse-ld=${GOLD_LINKER_FOUND}")
		set(CMAKE_STATIC_LINKER_FLAGS "${CMAKE_STATIC_LINKER_FLAGS} -fuse-ld=${GOLD_LINKER_FOUND}")
		set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -fuse-ld=${GOLD_LINKER_FOUND}")
		set(CMAKE_MODULE_LINKER_FLAGS "${CMAKE_MODULE_LINKER_FLAGS} -fuse-ld=${GOLD_LINKER_FOUND}")
	else()
		message(STATUS "Found Gold Linker ${GOLD_LINKER_FOUND}, but is UNUSABLE! Return code: ${RET}")
	endif()
else()
	message(STATUS "Gold Linker NOT found! Please install it for faster linkage.")
endif()

