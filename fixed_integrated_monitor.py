#!/usr/bin/env python3
"""
🚀 완전히 수정된 ex-GPT 고성능 모니터
- 올바른 API 스키마 적용 ✅
- 89 QPS + 100% 성공률 목표
- 즉시 실행 가능
"""

import asyncio
import aiohttp
import pandas as pd
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging
from collections import deque

class CompleteFixedGPUMonitor:
    """완전히 수정된 GPU 최적화 모니터"""
    
    def __init__(self):
        self.config = {
            # ✅ 수정된 API URL
            'API_URL': 'http://1.215.235.250:28080/v1/chat',
            'TARGET_QPS': 35,
            'MAX_QUERIES': 20,
            'TARGET_TIME': 60,
            
            # 🔥 최적화된 동시성
            'INITIAL_CONCURRENT': 10,
            'MAX_CONCURRENT': 50,
            'MIN_CONCURRENT': 5,
            
            # ⚡ 타이밍 최적화
            # 초기에는 백엔드 안정성을 위해 0.4초 지연을 두었으나
            # 현재는 불필요하여 0초로 설정
            'INITIAL_DELAY': 0,
            'TIMEOUT': 10.0,
            'CONNECT_TIMEOUT': 3.0,
            'READ_TIMEOUT': 7.0,
            'MAX_RETRIES': 3,
            
            # 🌐 네트워크 최적화
            'MAX_CONNECTIONS': 200,
            'MAX_CONNECTIONS_PER_HOST': 100,
            'KEEPALIVE_TIMEOUT': 30,
            
            # 📁 파일 설정
            'EXCEL_FILE': './queries.xlsx',
            'EXCEL_SHEET': 'sheet1',
            'QUERY_COLUMN': 1,
            
            # 🔄 동적 조정
            'AUTO_SCALING': True,
            'SUCCESS_RATE_THRESHOLD': 80,
            'QPS_THRESHOLD': 30,
        }
        
        # 📊 성능 데이터
        self.completed_requests = deque(maxlen=10000)
        self.start_time = time.time()
        self.current_concurrent = self.config['INITIAL_CONCURRENT']
        self.last_adjustment = time.time()
        self.semaphore = None
        self.active_requests = {}
        
        # 📁 로그 설정
        self.setup_logging()
        self.monitoring_active = False
        
        # 🎯 성능 통계
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'current_qps': 0,
            'peak_qps': 0,
            'average_response_time': 0,
            'success_rate': 0,
            'elapsed_time': 0
        }

    def setup_logging(self):
        """로깅 설정"""
        today = datetime.now().strftime('%Y-%m-%d_%H-%M')
        self.log_dir = Path(f'./fixed-gpu-monitor-{today}')
        self.log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / 'performance.log', encoding='utf-8'),
            ]
        )
        self.logger = logging.getLogger(__name__)

    def create_correct_api_request(self, query: str, index: int) -> Dict[str, Any]:
        """✅ 올바른 API 스키마에 맞는 요청 생성"""
        return {
                  "message_id": f"msg_{index}",
                  "session_id": f"session_{index}",
                  "user_id": f"user_{index % 50}",
                  "department": "성능테스트부서",
                  "authorization": "Bearer perf_token",
                  "stream": False,
                  "search_documents": False,
                  "search_scope": ["test_scope"],
                  "history": [
                      {
                          "role": "user",
                          "content": query
                      }
                  ],
                  "search_config": {
                      "max_documents": 20,
                      "min_relevance_score": 0.4,
                      "document_types": ["test"],
                      "date_range": {
                          "additionalProp1": "2020-01-01",
                          "additionalProp2": "2025-12-31",
                          "additionalProp3": ""
                      },
                      "priority_sources": ["test_source"],
                      "do_rerank": True
                  },
                  "response_format": {
                      "type": "markdown",
                      "max_length": 2000,
                      "include_citations": True,
                      "language": "ko",
                      "tone": "formal",
                      "instruction": "",
                      "encode_download_url_key": False
                  },
                  "max_context_tokens": 10000,
                  "temperature": 0.3,
                  "suggest_questions": False,
                  "generate_search_query": True
              }

    def calculate_performance_metrics(self):
        """성능 지표 계산"""
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        if elapsed <= 0:
            return
        
        total = len(self.completed_requests)
        success = sum(1 for r in self.completed_requests if r.get('success', False))
        
        # 최근 10초 기준 QPS
        recent_requests = [r for r in self.completed_requests 
                          if current_time - r.get('completion_time', 0) <= 10]
        current_qps = len(recent_requests) / min(10, elapsed)
        
        # 평균 응답 시간
        if success > 0:
            avg_response = sum(r.get('response_time', 0) for r in self.completed_requests 
                             if r.get('success', False)) / success
        else:
            avg_response = 0
        
        self.stats.update({
            'total_requests': total,
            'successful_requests': success,
            'failed_requests': total - success,
            'current_qps': current_qps,
            'peak_qps': max(self.stats['peak_qps'], current_qps),
            'average_response_time': avg_response,
            'success_rate': (success / total * 100) if total > 0 else 0,
            'elapsed_time': elapsed
        })

    def adjust_concurrency(self):
        """동적 동시성 조정"""
        if not self.config['AUTO_SCALING']:
            return
        
        current_time = time.time()
        if current_time - self.last_adjustment < 5:  # 5초마다 조정
            return
        
        success_rate = self.stats.get('success_rate', 0)
        current_qps = self.stats.get('current_qps', 0)
        
        old_concurrent = self.current_concurrent
        
        if success_rate > 95 and current_qps < self.config['TARGET_QPS']:
            # 높은 성공률 + 낮은 QPS → 동시성 증가
            self.current_concurrent = min(
                self.current_concurrent + 10,
                self.config['MAX_CONCURRENT']
            )
        elif success_rate < self.config['SUCCESS_RATE_THRESHOLD']:
            # 낮은 성공률 → 동시성 감소
            self.current_concurrent = max(
                self.current_concurrent - 5,
                self.config['MIN_CONCURRENT']
            )
        
        if old_concurrent != self.current_concurrent:
            self.logger.info(f"🔄 동시성 조정: {old_concurrent} → {self.current_concurrent}")
            self.logger.info(f"📊 성공률: {success_rate:.1f}%, QPS: {current_qps:.1f}")
            if self.semaphore is not None:
                # 세마포어 용량을 최신 동시성에 맞춰 재생성
                self.semaphore = asyncio.Semaphore(self.current_concurrent)
        
        self.last_adjustment = current_time

    def print_realtime_status(self):
        """실시간 상태 출력"""
        self.calculate_performance_metrics()
        
        print(f"\n{'='*80}")
        print(f"🚀 완전 수정된 GPU 모니터링 [{datetime.now().strftime('%H:%M:%S')}]")
        print(f"{'='*80}")
        
        progress = (len(self.completed_requests) / self.config['MAX_QUERIES']) * 100
        eta = (self.config['MAX_QUERIES'] - len(self.completed_requests)) / max(self.stats['current_qps'], 1)
        
        print(f"🎯 목표 진행률: {progress:.1f}% ({len(self.completed_requests)}/{self.config['MAX_QUERIES']})")
        print(f"⏱️ 목표 시간: {self.config['TARGET_TIME']}초 | 경과: {self.stats['elapsed_time']:.1f}초")
        print(f"🔮 완료 예상: {eta:.1f}초 후")
        
        print(f"\n📊 실시간 성능:")
        print(f"   🚀 현재 QPS: {self.stats['current_qps']:.1f} (목표: {self.config['TARGET_QPS']})")
        print(f"   🏆 최고 QPS: {self.stats['peak_qps']:.1f}")
        print(f"   ✅ 성공률: {self.stats['success_rate']:.1f}%")
        print(f"   ⚡ 평균 응답: {self.stats['average_response_time']:.2f}초")
        print(f"   🔄 동시 처리: {self.current_concurrent}개 (활성: {len(self.active_requests)})")
        
        # 🎯 목표 달성 여부
        if self.stats['current_qps'] >= self.config['TARGET_QPS']:
            print(f"   🎉 목표 QPS 달성!")
        if self.stats['success_rate'] >= 90:
            print(f"   🎉 높은 성공률 달성!")
        
        # 🚨 경고 상황
        if self.stats['success_rate'] < 80:
            print(f"   🚨 낮은 성공률 경고!")
        if eta > self.config['TARGET_TIME']:
            print(f"   ⚠️ 목표 시간 초과 예상!")

    def start_monitoring(self):
        """모니터링 시작"""
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                self.print_realtime_status()
                self.adjust_concurrency()
                time.sleep(2)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

    async def send_request(self, session: aiohttp.ClientSession,
                          query: str, index: int) -> Dict[str, Any]:
        """개별 요청 전송"""

        req_id = f"{index:04d}"
        start_time = time.time()

        self.active_requests[req_id] = {
            'query': query,
            'start_time': start_time,
            'index': index
        }
        last_error = None
        for attempt in range(1, self.config.get('MAX_RETRIES', 1) + 1):
            try:
                request_body = self.create_correct_api_request(query, index)

                async with session.post(
                    self.config['API_URL'],
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(
                        total=self.config['TIMEOUT'],
                        connect=self.config['CONNECT_TIMEOUT'],
                        sock_read=self.config['READ_TIMEOUT']
                    )
                ) as response:
                    response_time = time.time() - start_time
                    completion_time = time.time()

                    if response.status == 200:
                        try:
                            response_data = await response.json()
                            print(f"✅ 성공 [{index}]: {response_data}")
                            result = {
                                'index': index,
                                'query': query,
                                'success': True,
                                'response_time': response_time,
                                'completion_time': completion_time,
                                'status': response.status
                            }
                        except Exception as e:
                            print(f"💥 JSON 파싱 실패 [{index}] : {e}")
                            result = {
                                'index': index,
                                'query': query,
                                'success': False,
                                'response_time': response_time,
                                'completion_time': completion_time,
                                'error': f"JSON 파싱 실패: {e}"
                            }
                    else:
                        error_text = await response.text()
                        print(f"💥 실패 [{index}] - HTTP {response.status} - 응답: {error_text[:200]}")
                        result = {
                            'index': index,
                            'query': query,
                            'success': False,
                            'response_time': response_time,
                            'completion_time': completion_time,
                            'error': f"HTTP {response.status} - {error_text[:100]}"
                        }

                    if req_id in self.active_requests:
                        del self.active_requests[req_id]
                    self.completed_requests.append(result)

                    return result

            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                last_error = e
                if attempt < self.config.get('MAX_RETRIES', 1):
                    print(f"⏳ 타임아웃 [{index}] 재시도 {attempt}/{self.config['MAX_RETRIES']}")
                    await asyncio.sleep(1)
                    continue
            except Exception as e:
                last_error = e
                break

        if req_id in self.active_requests:
            del self.active_requests[req_id]

        result = {
            'index': index,
            'query': query,
            'success': False,
            'response_time': time.time() - start_time,
            'completion_time': time.time(),
            'error': str(last_error) if last_error else 'unknown'
        }
        self.completed_requests.append(result)
        return result
    
    async def run_fixed_test(self, queries: List[str]):
        """수정된 테스트 실행"""
        
        print(f"🚀 완전 수정된 GPU 최적화 테스트 시작!")
        print(f"🎯 목표: {len(queries)}개 질의를 {self.config['TARGET_TIME']}초 안에 처리")
        print(f"📊 목표 QPS: {self.config['TARGET_QPS']:.1f}")
        print(f"🔧 올바른 API 스키마 적용")
        print(f"⚡ 자동 스케일링: {'✅' if self.config['AUTO_SCALING'] else '❌'}")
        
        # 모니터링 시작
        self.start_monitoring()
        
        # 최적화된 커넥터 설정
        connector = aiohttp.TCPConnector(
            limit=self.config['MAX_CONNECTIONS'],
            limit_per_host=self.config['MAX_CONNECTIONS_PER_HOST'],
            keepalive_timeout=self.config['KEEPALIVE_TIMEOUT'],
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.config['TIMEOUT'],
            connect=self.config['CONNECT_TIMEOUT']
        )
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'FixedGPUMonitor/1.0'}
        ) as session:
            
            # 동적 세마포어
            self.semaphore = asyncio.Semaphore(self.current_concurrent)


            async def process_query_with_semaphore(query: str, index: int):
              async with self.semaphore:
                  await asyncio.sleep(self.config['INITIAL_DELAY'])
                  return await self.send_request(session, query, index)
            
            print(f"🔄 3초 후 시작...")
            await asyncio.sleep(3)
            
            # 모든 요청 동시 실행
            tasks = [process_query_with_semaphore(query, i+1) 
                    for i, query in enumerate(queries)]
            
            # 진행률 추적
            for i, task in enumerate(asyncio.as_completed(tasks)):
                await task
                if (i + 1) % 100 == 0:  # 100개마다 로그
                    elapsed = time.time() - self.start_time
                    current_qps = len(self.completed_requests) / elapsed if elapsed > 0 else 0
                    self.logger.info(f"진행: {i+1}/{len(tasks)}, QPS: {current_qps:.1f}")
        
        # 모니터링 중지
        self.monitoring_active = False
        
        # 최종 결과
        self.print_final_results()

    def print_final_results(self):
        """최종 결과 분석"""
        self.calculate_performance_metrics()
        
        print(f"\n{'='*80}")
        print(f"🎯 완전 수정된 테스트 최종 결과")
        print(f"{'='*80}")
        
        total_time = self.stats['elapsed_time']
        achieved_qps = self.stats['total_requests'] / total_time if total_time > 0 else 0
        
        print(f"📊 처리 결과:")
        print(f"   총 처리: {self.stats['total_requests']}개")
        print(f"   성공: {self.stats['successful_requests']}개")
        print(f"   실패: {self.stats['failed_requests']}개")
        print(f"   성공률: {self.stats['success_rate']:.1f}%")
        
        print(f"\n⚡ 성능 결과:")
        print(f"   실제 QPS: {achieved_qps:.1f} (목표: {self.config['TARGET_QPS']})")
        print(f"   최고 QPS: {self.stats['peak_qps']:.1f}")
        print(f"   총 소요 시간: {total_time:.1f}초 (목표: {self.config['TARGET_TIME']}초)")
        print(f"   평균 응답 시간: {self.stats['average_response_time']:.2f}초")
        
        # 🎯 목표 달성 평가
        qps_achieved = achieved_qps >= self.config['TARGET_QPS']
        time_achieved = total_time <= self.config['TARGET_TIME']
        success_rate_good = self.stats['success_rate'] >= 90
        
        print(f"\n🎯 목표 달성 평가:")
        print(f"   QPS 목표: {'✅ 달성' if qps_achieved else '❌ 미달'}")
        print(f"   시간 목표: {'✅ 달성' if time_achieved else '❌ 초과'}")
        print(f"   성공률: {'✅ 우수' if success_rate_good else '⚠️ 개선필요'}")
        
        overall_success = qps_achieved and time_achieved and success_rate_good
        print(f"   🏆 종합 평가: {'🎉 완전 성공!' if overall_success else '📈 개선 필요'}")
        
        # 결과 저장
        self.save_results()

    def save_results(self):
        """결과 저장"""
        report = {
            'config': self.config,
            'final_stats': self.stats,
            'completed_requests': list(self.completed_requests),
            'timestamp': datetime.now().isoformat()
        }
        
        report_file = self.log_dir / 'fixed_performance_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"💾 성능 보고서: {report_file}")

    def load_queries(self) -> List[str]:
        """질의 로드"""
        try:
            df = pd.read_excel(self.config['EXCEL_FILE'], sheet_name=self.config['EXCEL_SHEET'])
            queries = df.iloc[:, self.config['QUERY_COLUMN']].dropna().astype(str).tolist()
            queries = [q.strip() for q in queries if len(q.strip()) > 3]
            return queries[:self.config['MAX_QUERIES']]
        except Exception as e:
            print(f"⚠️ 엑셀 로드 실패: {e}")
            # 기본 테스트 질의 생성
            return [f"테스트 질의 {i+1}: 도로 관련 정보를 알려주세요." for i in range(100)]

async def main():
    """메인 실행"""
    print('🚀 완전 수정된 ex-GPT GPU 최적화 모니터링')
    print('🎯 목표: 89 QPS + 100% 성공률')
    print('✅ 올바른 API 스키마 적용')
    print(f'시작: {datetime.now().strftime("%Y.%m.%d %H:%M:%S")}')
    
    monitor = CompleteFixedGPUMonitor()
    
    queries = monitor.load_queries()
    print(f"✅ {len(queries)}개 질의 로드 완료")
    
    if len(queries) < monitor.config['MAX_QUERIES']:
        print(f"⚠️ 요청한 {monitor.config['MAX_QUERIES']}개보다 적은 {len(queries)}개만 로드됨")
        monitor.config['MAX_QUERIES'] = len(queries)
        monitor.config['TARGET_QPS'] = len(queries) / monitor.config['TARGET_TIME']
        print(f"🔄 목표 QPS 자동 조정: {monitor.config['TARGET_QPS']:.1f}")
    
    await monitor.run_fixed_test(queries)
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)