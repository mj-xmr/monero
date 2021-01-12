// Copyright (c) 2014-2020, The Monero Project
// 
// All rights reserved.
// 
// Redistribution and use in source and binary forms, with or without modification, are
// permitted provided that the following conditions are met:
// 
// 1. Redistributions of source code must retain the above copyright notice, this list of
//    conditions and the following disclaimer.
// 
// 2. Redistributions in binary form must reproduce the above copyright notice, this list
//    of conditions and the following disclaimer in the documentation and/or other
//    materials provided with the distribution.
// 
// 3. Neither the name of the copyright holder nor the names of its contributors may be
//    used to endorse or promote products derived from this software without specific
//    prior written permission.
// 
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
// EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
// MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
// THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
// PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
// STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
// THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
// 
// Parts of this file are originally copyright (c) 2012-2013 The Cryptonote developers

#pragma once
#include <memory>
#include "serialization.h"

namespace serialization
{
  namespace detail
  {
    template <typename Archive, class T>
    bool serialize_pair_element(Archive& ar, T& e)
    {
      return ::do_serialize(ar, e);
    }

#define PAIR_VARINT_SERIALIZER(type) \
    template <typename Archive> \
    bool serialize_pair_element(Archive& ar, type& e) \
    { \
      ar.serialize_varint(e); \
      return true; \
    }

#define PAIR_VARINT_SERIALIZER_2(signed_type, unsigned_type) \
  PAIR_VARINT_SERIALIZER(unsigned_type) \
  template<typename Archive> \
  bool serialize_pair_element(Archive& ar, signed_type& e) \
  { \
    return serialize_container_element(ar, *(typename boost::make_unsigned<signed_type>::type *)(&e)); \
  }

PAIR_VARINT_SERIALIZER_2(int64_t, uint64_t)
PAIR_VARINT_SERIALIZER_2(int32_t, uint32_t)
PAIR_VARINT_SERIALIZER_2(int16_t, uint16_t)
#ifdef __APPLE__
PAIR_VARINT_SERIALIZER_2(ssize_t, size_t)
#endif
}

template <template <bool> class Archive, class F, class S>
inline bool do_serialize(Archive<false>& ar, std::pair<F,S>& p)
{
  size_t cnt;
  ar.begin_array(cnt);
  if (!ar.stream().good())
    return false;
  if (cnt != 2)
    return false;

  if (!::serialization::detail::serialize_pair_element(ar, p.first))
    return false;
  if (!ar.stream().good())
    return false;
  ar.delimit_array();
  if (!::serialization::detail::serialize_pair_element(ar, p.second))
    return false;
  if (!ar.stream().good())
    return false;

  ar.end_array();
  return true;
}

template <template <bool> class Archive, class F, class S>
inline bool do_serialize(Archive<true>& ar, std::pair<F,S>& p)
{
  ar.begin_array(2);
  if (!ar.stream().good())
    return false;
  if(!::serialization::detail::serialize_pair_element(ar, p.first))
    return false;
  if (!ar.stream().good())
    return false;
  ar.delimit_array();
  if(!::serialization::detail::serialize_pair_element(ar, p.second))
    return false;
  if (!ar.stream().good())
    return false;
  ar.end_array();
  return true;
}

