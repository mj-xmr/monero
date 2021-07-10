// Copyright (c) 2006-2013, Andrey N. Sabelnikov, www.sabelnikov.net
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
// * Redistributions of source code must retain the above copyright
// notice, this list of conditions and the following disclaimer.
// * Redistributions in binary form must reproduce the above copyright
// notice, this list of conditions and the following disclaimer in the
// documentation and/or other materials provided with the distribution.
// * Neither the name of the Andrey N. Sabelnikov nor the
// names of its contributors may be used to endorse or promote products
// derived from this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER  BE LIABLE FOR ANY
// DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
// ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
// SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//


#ifndef _MISC_LOG_EX_MIN_H_
#define _MISC_LOG_EX_MIN_H_

#ifdef __cplusplus

#include <string>
#include <sstream>

#include "easylogging++_base.h"

#include "misc_log_ex_defaults.h"
    
#ifdef MCLOG_TYPE
    #undef MCLOG_TYPE
#endif // MCLOG_TYPE
#define MCLOG_TYPE(level, cat, color, type, x) do { \
    if (el::ILoggers::allowed(level, cat)) { \
      el::base::IWriterBasic::create(level, color, __FILE__, __LINE__, ELPP_FUNC, type)->construct(cat) << x; \
    } \
  } while (0)
  
#include "misc_log_ex_common.h"

extern "C"
{

#endif

#ifdef __GNUC__
#define ATTRIBUTE_PRINTF __attribute__((format(printf, 2, 3)))
#else
#define ATTRIBUTE_PRINTF
#endif

bool merror(const char *category, const char *format, ...) ATTRIBUTE_PRINTF;
bool mwarning(const char *category, const char *format, ...) ATTRIBUTE_PRINTF;
bool minfo(const char *category, const char *format, ...) ATTRIBUTE_PRINTF;
bool mdebug(const char *category, const char *format, ...) ATTRIBUTE_PRINTF;
bool mtrace(const char *category, const char *format, ...) ATTRIBUTE_PRINTF;

#ifdef __cplusplus

}

#endif

#endif //_MISC_LOG_EX_H_
