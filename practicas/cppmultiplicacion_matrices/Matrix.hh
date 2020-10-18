#ifndef MATRIX_HH
#define MATRIX_HH

#include <vector>
#include <iostream>
#include <cassert>
#include "Threadpool.hh"
#include <chrono>
#include <random>

template <typename T>
class Matrix{
    private:
        size_t rows;
        size_t cols;
        std::vector <T> data;
        T computeCell(Matrix *thismatrix, Matrix &other, size_t i, size_t j){
            T result = 0;
            for (size_t index = 0; index < thismatrix->cols; index++)
                result+= thismatrix->data.at((i*thismatrix-> rows)+index) * other[index][j];
            return result;
        }
        std::vector<T> computeCol(Matrix *thismatrix, std::vector <T> &other){
            std::vector <T> results; 
            for (size_t index = 0; index <other.size(); index++){
                T res = 0;
                for(size_t j = 0; j < thismatrix->rows ; j++){
                    res += thismatrix->data.at((index*thismatrix-> rows) + j) * other.at(j) ;
                }
                results.insert(results.begin()+index, res);
            }
            return results;

        }
        void assignCol (std::vector <T> &other, size_t r){
            for(size_t j = 0; j < rows ; j++)
                data.at((j*rows)+r) = other.at(j);
        }
    public:
        Matrix(size_t n, size_t m)
            : rows(n),
            cols(m),
            data(n * m)
            {
            }
        std::vector <T> getCol(size_t r){
            std::vector <T> gcol;
            for (size_t i = 0; i < rows; i++){
                gcol.insert(gcol.begin()+i, data.at((i) * rows + r));
            }
            return gcol;
        }
        //https://stackoverflow.com/questions/18985538/how-to-fill-an-array-with-random-floating-point-numbers
        void fill(){
            std::default_random_engine generator;
            std::uniform_real_distribution<double> distribution(0.0,100);
             for (size_t i = 0; i < this->rows; i++)
                for(size_t j = 0; j < this->cols; j++)       
                    data.insert(data.begin() + i*this->rows + j,(T)distribution(generator));
        }

        T * operator[](size_t index){
            assert(index<=rows);
            return &data.at(index*rows);
        }

        friend std::ostream &operator <<(std::ostream &os, Matrix & m) { 
            os << std::endl;
            for (int i = 0; i < m.rows; i++){
                os<<"[";
                for(int j = 0; j < m.cols; j++){
                    os << m[i][j];
                   auto s = (j!= m.cols-1)? "\t":"";
                    os << s;
                }
                os <<"]" << std::endl;
            }
            return os;
            } 

        Matrix mult(Matrix &other){
            Matrix <T> multresult(this->rows, other.cols);
            
            //for non-threaded executions
            // for(size_t i =0; i< this->rows; i++)
            //     for(size_t j = 0; j< other.cols; j++){
            //         multresult[i][j] = this->computeCell(this, other, i, j);
            //     }
            
            {
            ThreadPool pool(4);
            
            for (size_t i = 0; i < this->rows; i++)
                for (size_t j = 0; j < other.cols; j++){
                        pool.enqueue([&multresult,  i, j, this, &other]  {
                            multresult[i][j] = this->computeCell(this, other, i, j);
                        });
                }

            }
                
            return multresult;   
        }

        Matrix mult2(Matrix &other){
            Matrix <T> multresult(this->rows, other.cols);
            {            
            ThreadPool pool(4);
            for(size_t i = 0; i< cols; i++){
                    pool.enqueue([ &multresult, i, this, &other]{
                        std::vector <T> r = other.getCol(i);
                        std::vector <T> res = computeCol(this,r);
                        multresult.assignCol(res,i);
                    });
                }
            }
          
            return multresult;  

            // For non-threaded execution
            // for(size_t i = 0; i< cols; i++){
            //     std::vector <T> r = other.getCol(i);
            //     std::vector <T> res = computeCol(this,r);
            //         for(T num: res)
            //             std::cout<<num<<"\t";
            //     std::cout<<std::endl;
            //     multresult.assignCol(res,i);
            //     // std::cout<<multresult;
            // }
        }
        
        

};



#endif